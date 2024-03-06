import socket
from Packet import Packet
from PacketProcessor import PacketProcessor
from packet_constants import OP, AC

class EOSocket:
    def __init__(self, sock=None, client=False):
        self.processor = PacketProcessor(client)
        self.client = client
        self.socket = sock if sock is not None else socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sendbuf = b''
        self.recvbuf = b''

    def connect(self, address, port):
        self.socket.connect((address, port))

    def bind(self, address, port):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((address, port))

    def listen(self, backlog=1):
        self.socket.listen(backlog)

    def accept(self):
        client_socket, _ = self.socket.accept()
        return EOSocket(client_socket, True)

    def close(self):
        if self.socket is not None:
            self.socket.close()
            self.recvbuf = b""
            self.sendbuf = b""
            self.socket = None

    def is_closed(self):
        return self.socket is None

    def get_peer_name(self):
        return self.socket.getpeername()[0] if self.socket else None

    def do_recv(self):
        data = self.socket.recv(65536)
        if not data:
            self.close()
            return 0
        self.recvbuf += data
        return len(data)

    def do_send(self):
        sent = self.socket.send(self.sendbuf)
        self.sendbuf = self.sendbuf[sent:]

    def need_send(self):
        return len(self.sendbuf) > 0

    def send(self, data):
        self.sendbuf += data

    def get_packet(self):
        if len(self.recvbuf) < 2:
            return None
        length = Packet.number(self.recvbuf[0], self.recvbuf[1])
        if len(self.recvbuf) < length + 2:
            return None
        rawdata = self.recvbuf[2:length + 2]
        decdata = self.processor.decode(rawdata)
        self.recvbuf = self.recvbuf[length + 2:]
        packet = Packet(decdata, self.client)
        if self.client:
            self.processor.scrape_client_packet(packet)
        else:
            self.processor.scrape_server_packet(packet)
        return packet

    def send_packet(self, packet):
        if not self.client and not (packet.family() == AC.INIT.value and packet.action() == OP.INIT.value):
            packet.set_sequence(self.processor.gen_sequence())
        else:
            self.processor.gen_sequence()
        rawdata = packet.serialize()
        encdata = rawdata[:2] + self.processor.encode(rawdata[2:])
        self.send(encdata)
