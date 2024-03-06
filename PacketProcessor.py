from packet_constants import OP, AC

class PacketProcessor:
    challenge = -1
    server_encval = -1
    client_encval = -1
    seq_start = -1
    seq = 0

    def __init__(self, client):
        self.is_client = client  # True if client socket, False for server socket

    def init_sequence(self, s1, s2):
        PacketProcessor.seq_start = s1 * 7 + s2 - 13

    def update_sequence(self, s1, s2):
        PacketProcessor.seq_start = max(s1 - s2, 0)

    def gen_sequence(self):
        result = 81 + PacketProcessor.seq_start + PacketProcessor.seq if PacketProcessor.seq_start + PacketProcessor.seq < 0 else PacketProcessor.seq_start + PacketProcessor.seq
        PacketProcessor.seq = (PacketProcessor.seq + 1) % 10
        return result % 253

    def has_encryption(self):
        return PacketProcessor.server_encval >= 0 and PacketProcessor.client_encval >= 0

    def remember_challenge(self, challenge):
        PacketProcessor.challenge = challenge

    def setup_encryption_from_init(self, server_encval, client_encval):
        if PacketProcessor.challenge < 0:
            raise Exception("RememberChallenge was not called before SetupEncryptionFromInit")
        PacketProcessor.server_encval = server_encval
        PacketProcessor.client_encval = client_encval + PacketProcessor.challenge % 11

    def update_encryption_from_client(self, n):
        PacketProcessor.client_encval += n

    def update_encryption_from_server(self, n):
        PacketProcessor.server_encval += n + PacketProcessor.client_encval % 50

    def scrape_client_packet(self, packet):
        if not self.has_encryption() and packet.family() == OP.INIT.value and packet.action() == AC.INIT.value:
            challenge = packet.get_three()
            self.remember_challenge(challenge)
        elif self.has_encryption() and packet.family() == OP.PLAY.value and packet.action() == AC.REQUEST.value:
            packet.get_int()  # char_id, assuming it's being consumed for some purpose
            n = packet.get_char()
            self.update_encryption_from_client(n)

    def scrape_server_packet(self, packet):
        if not self.has_encryption() and packet.family() == OP.INIT.value and packet.action() == AC.INIT.value:
            init_reply = packet.get_byte()
            if init_reply == 2:  # INIT_OK
                seq1 = packet.get_byte()
                seq2 = packet.get_byte()
                server_encval = packet.get_short()
                client_encval = packet.get_short()
                self.init_sequence(seq1, seq2)
                self.setup_encryption_from_init(server_encval, client_encval)
        elif self.has_encryption() and packet.family() == OP.SECURITY.value and packet.action() == AC.SET.value:
            seq1 = packet.get_short()
            seq2 = packet.get_char()
            self.update_sequence(seq1, seq2)
        elif self.has_encryption() and packet.family() == OP.PLAY.value and packet.action() == AC.CONFIRM.value:
            n = packet.get_char()
            self.update_encryption_from_server(n)

    def encode(self, b):
        if b[0] == OP.INIT.value and b[1] == AC.INIT.value:
            return b

        if not self.has_encryption():
            raise Exception("Encryption parameters not set")

        encval = PacketProcessor.server_encval if self.is_client else PacketProcessor.client_encval

        enckey_table = [
            lambda i: -(i + 0x74),
            lambda i: +(encval // 253),
            lambda i: -((encval - 1) % 253),
        ]

        # Create a bytearray for mutable sequence of bytes
        b = bytearray(b)

        for i in range(1, len(b)):
            # Directly use the byte value, no need for ord()
            val = b[i - 1]
            val = (val + enckey_table[i % 3](i)) & 0xFF
            b[i - 1] = val

        # Convert bytearray back to bytes before returning
        return bytes(b)

    def decode(self, b):
        if b[0] == OP.INIT.value and b[1] == AC.INIT.value:
            return b

        if not self.has_encryption():
            raise Exception("Encryption parameters not set")

        decval = PacketProcessor.client_encval if self.is_client else PacketProcessor.server_encval

        deckey_table = [
            lambda i: +(i + 0x74),
            lambda i: -(decval // 253),
            lambda i: +((decval - 1) % 253),
        ]

        # Create a bytearray for mutable sequence of bytes
        b = bytearray(b)

        for i in range(1, len(b)):
            # Directly use the byte value, no need for ord()
            val = b[i - 1]
            val = (val + deckey_table[i % 3](i)) & 0xFF
            b[i - 1] = val

        # Convert bytearray back to bytes
        return bytes(b)
