import select
import importlib
import threading
from ui.PacketEditorGUI import PacketEditorGUI
from net.PacketProcessor import PacketProcessor
from net.EOSocket import EOSocket
from net.packet_constants import AC, OP

class EOProxy:
    def __init__(self):
        self.server = None
        self.client = None
        self.gui = None

    def start_gui(self):
        def gui_thread_func():
            self.gui = PacketEditorGUI(self.on_packet_edit, self.on_gui_close)
            self.gui.run()

        self.gui_thread = threading.Thread(target=gui_thread_func, daemon=False)
        self.gui_thread.start()

    def on_packet_edit(self, packet, is_client):
        if is_client:
            self.send_to_server(packet)
        else:
            self.send_to_client(packet)

    def on_gui_close(self):
        print("Shutting down the proxy due to GUI closure.")
        if self.client:
            self.client.close()
        elif self.server:
            self.server.close()
        exit(0)

    def send_to_client(self, packet):
        self.present_packet(packet, False, True)
        self.client.send_packet(packet)

    def send_to_server(self, packet):
        self.present_packet(packet, True, True)
        self.server.send_packet(packet)

    def present_packet(self, packet, is_client, is_proxy=False):
        direction = "C" if is_client else "S"
        try:
            op_name = OP(packet.family()).name
        except ValueError:
            op_name = f"Unknown_OP_{packet.family()}"
        
        try:
            ac_name = AC(packet.action()).name
        except ValueError:
            ac_name = f"Unknown_AC_{packet.action()}"

        formatted_direction = f"{'<' if is_proxy else '['}{direction}->{'C' if not is_client else 'S'}{'>' if is_proxy else ']'}"
        packet_data_hex = packet.data.hex()
        if self.gui:
            self.gui.master.after(0, self.gui.add_packet, formatted_direction, op_name, ac_name, packet.family(), packet.action(), packet_data_hex)

        packet_name = f"{direction}_{op_name}_{ac_name}"
        module_name = f"handlers.{packet_name}"

        print(f"{formatted_direction} {packet_name.replace('_', ' ')} (length={len(packet.data)})")
        print(' '.join(f"{x:02X}" for x in packet.data))

        try:
            handler_module = importlib.import_module(module_name)
            if hasattr(handler_module, 'handle'):
                handler_module.handle(self, packet)
            else:
                print(f"Handler function not found in module {module_name}")
        except ModuleNotFoundError as e:
            print(f"No specific handler found for {packet_name}. Packet data: {' '.join(f'{x:02X}' for x in packet.data)}")

    def wait_for_connect(self, local_address, local_port, remote_address, remote_port):
        listener = EOSocket(None, False, self)
        listener.bind(local_address, local_port)
        listener.listen(1)
        print(f"Listening on {local_address}:{local_port}...")
        self.client = listener.accept()
        print("Client connected")
        listener.close()
        
        self.server = EOSocket(None, False, self)
        print(f"Connecting to server: {remote_address}:{remote_port}...")
        self.server.connect(remote_address, remote_port)
        print("Connected to server")

    def pump_networking(self):
        while True:
            read_sockets = []
            write_sockets = []
            if not self.client.is_closed():
                read_sockets.append(self.client.socket)
                if self.client.need_send():
                    write_sockets.append(self.client.socket)
            if not self.server.is_closed():
                read_sockets.append(self.server.socket)
                if self.server.need_send():
                    write_sockets.append(self.server.socket)
            
            if not read_sockets and not write_sockets:
                print("Both sockets closed.")
                break
            
            readable, writable, _ = select.select(read_sockets, write_sockets, [], 0.1)
            
            if self.client.socket in readable:
                if self.client.do_recv() == 0:  # Client disconnected
                    self.client.close()
                    self.server.close()
                    break
                self.forward_packets(from_socket=self.client, to_socket=self.server)
            
            if self.server.socket in readable:
                if self.server.do_recv() == 0:  # Server disconnected
                    self.server.close()
                    self.client.close()
                    break
                self.forward_packets(from_socket=self.server, to_socket=self.client)

            if self.client.socket in writable:
                self.client.do_send()

            if self.server.socket in writable:
                self.server.do_send()
                
    def has_encryption(self):
        return PacketProcessor.server_encval >= 0 and PacketProcessor.client_encval >= 0

    def forward_packets(self, from_socket, to_socket):
        packet = from_socket.get_packet()
        while packet is not None:
            if from_socket == self.client:
                self.before_client_packet_forward(packet, from_socket)
            else:
                self.before_server_packet_forward(packet, from_socket)

            self.present_packet(packet, from_socket == self.client)
            to_socket.send_packet(packet)

            if from_socket == self.client:
                self.after_client_packet_forward(packet, from_socket)
            else:
                self.after_server_packet_forward(packet, from_socket)

            packet = from_socket.get_packet()

    def before_client_packet_forward(self, packet, from_socket):
        if not from_socket.processor.has_encryption() and packet.family() == OP.INIT.value and packet.action() == AC.INIT.value:
            challenge = packet.get_three()
            from_socket.processor.remember_challenge(challenge)

    def after_client_packet_forward(self, packet, from_socket):
        if from_socket.processor.has_encryption() and packet.family() == OP.PLAY.value and packet.action() == AC.REQUEST.value:
            packet.get_int()
            n = packet.get_char()
            from_socket.processor.update_encryption_from_client(n)

    def before_server_packet_forward(self, packet, from_socket):
        if not from_socket.processor.has_encryption() and packet.family() == OP.INIT.value and packet.action() == AC.INIT.value:
            init_reply = packet.get_byte()
            if init_reply == 2:  # INIT_OK
                seq1 = packet.get_byte()
                seq2 = packet.get_byte()
                server_encval = packet.get_short()
                client_encval = packet.get_short()
                from_socket.processor.init_sequence(seq1, seq2)
                from_socket.processor.setup_encryption_from_init(server_encval, client_encval)

    def after_server_packet_forward(self, packet, from_socket):
        if from_socket.processor.has_encryption() and packet.family() == OP.SECURITY.value and packet.action() == AC.SET.value:
            seq1 = packet.get_short()
            seq2 = packet.get_char()
            from_socket.processor.update_sequence(seq1, seq2)
        elif self.has_encryption() and packet.family() == OP.PLAY.value and packet.action() == AC.CONFIRM.value:
            n = packet.get_char()
            n += packet.get_char()
            from_socket.processor.update_encryption_from_server(n)

    def run_proxy(self, local_address, local_port, remote_address, remote_port):
        self.start_gui()
        self.wait_for_connect(local_address, local_port, remote_address, remote_port)
        self.pump_networking()
