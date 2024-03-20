from math import floor
from net.packet_constants import OP, AC

class PacketProcessor:
    challenge = -1
    server_encval = -1
    client_encval = -1
    seq_start = -1
    seq = 0
    ticker_decode = 0
    ticker_encode = 0
    ticker_enabled = False

    decodeVals = [
        0x49,  # I
        0x4D,  # M
        0x4E,  # N
        0x55,  # U
        0x54,  # T
        0x5F,  # _
        0x59,  # Y
        0x45,  # E
        0x53,  # S
        0x4D,  # M
        0x4F,  # O
        0x4D  # M
    ]

    def __init__(self, client):
        self.is_client = client

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
        PacketProcessor.extra_param = challenge % 252

    def setup_encryption_from_init(self, server_encval, client_encval):
        if PacketProcessor.challenge < 0:
            raise Exception("RememberChallenge was not called before SetupEncryptionFromInit")
        PacketProcessor.server_encval = server_encval
        PacketProcessor.client_encval = client_encval + (PacketProcessor.challenge % 11)

    def update_encryption_from_client(self, n):
        PacketProcessor.client_encval += n

    def update_encryption_from_server(self, n):
        PacketProcessor.server_encval += n + PacketProcessor.client_encval % 11

    @staticmethod
    def get_key_table(type, value):
        key_table = [
            lambda i: +floor(value / 253),
            lambda i: (-((value - 1) % 253)),
            lambda i: -(i - 0x79),
        ]

        if type == 'dec':
            key_table = [lambda i, fn=fn: -fn(i) for fn in key_table]
        elif type != 'enc':
            raise Exception(f"Invalid type: {type}. Expected 'enc' or 'dec'.")

        return key_table

    def encode(self, b):
        if b[0] == OP.INIT.value and b[1] == AC.INIT.value:
            return b

        if not self.has_encryption():
            raise Exception("Encryption parameters not set")

        encval = PacketProcessor.server_encval if self.is_client else PacketProcessor.client_encval
        b = bytearray(b)
        key_table = self.get_key_table('enc', encval)

        for i in range(1, len(b)):
            val = b[i - 1]
            val = (val + key_table[i % 3](i)) & 0xFF

            if not self.is_client and PacketProcessor.ticker_enabled:
                PacketProcessor.ticker_encode += 1
                if PacketProcessor.ticker_encode > len(self.decodeVals):
                    PacketProcessor.ticker_encode = 1
                val = (val + self.decodeVals[PacketProcessor.ticker_encode - 1]) & 0xFF

            b[i - 1] = val

        return bytes(b)

    def decode(self, b):
        if b[0] == OP.INIT.value and b[1] == AC.INIT.value:
            return b

        if not self.has_encryption():
            raise Exception("Encryption parameters not set")

        decval = PacketProcessor.client_encval if self.is_client else PacketProcessor.server_encval
        b = bytearray(b)
        key_table = self.get_key_table('dec', decval)

        for i in range(1, len(b)):
            val = b[i - 1]

            if self.is_client and PacketProcessor.ticker_enabled:
                PacketProcessor.ticker_decode += 1
                if PacketProcessor.ticker_decode > len(self.decodeVals):
                    PacketProcessor.ticker_decode = 1
                val = (val - self.decodeVals[PacketProcessor.ticker_decode - 1]) & 0xFF

            val = (val + key_table[i % 3](i)) & 0xFF
            b[i - 1] = val

        return bytes(b)
