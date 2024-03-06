import select
import importlib
from EOSocket import EOSocket
from packet_constants import AC, OP

class EOProxy:
    def __init__(self):
        self.server = None
        self.client = None

    def send_to_client(self, packet):
        # Assume packet.seek(0) resets the packet's internal pointer for reading
        self.present_packet(packet, False)
        self.client.send_packet(packet)

    def send_to_server(self, packet):
        self.present_packet(packet, True)
        self.server.send_packet(packet)

    def present_packet(self, packet, is_client):
        direction = "C" if is_client else "S"
        try:
            op_name = OP(packet.family()).name
        except ValueError:
            op_name = f"Unknown_OP_{packet.family()}"
        
        try:
            ac_name = AC(packet.action()).name
        except ValueError:
            ac_name = f"Unknown_AC_{packet.action()}"

        packet_name = f"{direction}_{op_name}_{ac_name}"
        module_name = f"handlers.{packet_name}"

        print(f"[{direction}->{'C' if not is_client else 'S'}] {packet_name.replace('_', ' ')} (length={len(packet.data)})")
        print(' '.join(f"{x:02X}" for x in packet.data))

        try:
            handler_module = importlib.import_module(module_name)
            # Assuming the handler function is named 'handle'
            if hasattr(handler_module, 'handle'):
                handler_module.handle(self, packet)
            else:
                print(f"Handler function not found in module {module_name}")
        except ModuleNotFoundError as e:
            print(f"No specific handler found for {packet_name}. Packet data: {' '.join(f'{x:02X}' for x in packet.data)}")

    def wait_for_connect(self, local_address, local_port, remote_address, remote_port):
        listener = EOSocket()
        listener.bind(local_address, local_port)
        listener.listen(1)
        print(f"Listening on {local_address}:{local_port}...")
        self.client = listener.accept()
        print("Client connected")
        listener.close()
        
        self.server = EOSocket()
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

    def forward_packets(self, from_socket, to_socket):
        packet = from_socket.get_packet()
        while packet is not None:
            self.present_packet(packet, from_socket == self.client)
            to_socket.send_packet(packet)
            packet = from_socket.get_packet()

    def run_proxy(self, local_address, local_port, remote_address, remote_port):
        self.wait_for_connect(local_address, local_port, remote_address, remote_port)
        self.pump_networking()
