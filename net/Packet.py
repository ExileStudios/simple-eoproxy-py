class Packet:
    PACKET_MAX1 = 253
    PACKET_MAX2 = 64009
    PACKET_MAX3 = 16194277
    PACKET_MAX4 = 4097152081

    @staticmethod
    def number(bit1=0, bit2=254, bit3=254, bit4=254, bit5=254):
        bits = [bit1, bit2, bit3, bit4, bit5]
        bits = [1 if b == 0 or b == 254 else b for b in bits]
        bits = [b-1 for b in bits]
        return sum(b * max_val for b, max_val in zip(bits, [1, Packet.PACKET_MAX1, Packet.PACKET_MAX2, Packet.PACKET_MAX3, Packet.PACKET_MAX4]))

    @staticmethod
    def enumber(number, size):
        max_vals = [Packet.PACKET_MAX1, Packet.PACKET_MAX2, Packet.PACKET_MAX3, Packet.PACKET_MAX4]
        b = [254] * size
        for i in range(4, 0, -1):
            if i >= size:
                if number >= max_vals[i-1]:
                    number %= max_vals[i-1]
            elif number >= max_vals[i-1]:
                b[i] = (int(number / max_vals[i-1]) + 1) & 0xFF
                number %= max_vals[i-1]
            else:
                b[i] = 254
        b[0] = (number + 1) & 0xFF
        return b

    @staticmethod
    def echar(number): return Packet.enumber(number, 1)

    @staticmethod
    def eshort(number): return Packet.enumber(number, 2)

    @staticmethod
    def ethree(number): return Packet.enumber(number, 3)

    @staticmethod
    def eint(number): return Packet.enumber(number, 4)

    @staticmethod
    def efive(number): return Packet.enumber(number, 5)

    def __init__(self, b=None, from_client=False):
        self.has_seq = False
        self.pos = 0
        self.seq = b""
        self.data = b""
        self.id = b"\xff\xff"
        if b is not None:
            self.id = b[:2]
            if from_client and not (b[0] == 255 and b[1] == 255):
                self.has_seq = True
                self.seq = b[2:3]
                self.data = b[3:]
            else:
                self.data = b[2:]

    def family(self):
        return self.id[1]

    def action(self):
        return self.id[0]

    def length(self):
        return len(self.data)

    def sequence(self):
        if self.has_seq:
            return Packet.number(self.seq[0])
        return False

    def set_sequence(self, seq):
        n = Packet.enumber(seq, 1)
        if self.has_seq:
            self.seq = bytes([n[0]])

    def data(self):
        return self.data

    def serialize(self):
        payload = self.id + self.seq + self.data
        return bytes(Packet.enumber(len(payload), 2)) + payload

    def seek(self, pos):
        self.pos = int(pos)

    def skip(self, n):
        self.pos += n
        
    def reset(self):
        self.data = b""
        self.pos = 0

    def set_id(self, family, action):
        self.id = bytes([action, family])

    def get_number(self, n):
        params = self.data[self.pos:self.pos+n]
        self.pos += n
        return Packet.number(*params)

    def peek_byte(self):
        if self.pos < len(self.data):
            return self.data[self.pos]
        else:
            return 0

    def remaining(self):
        return max(0, len(self.data) - self.pos)

    def get_byte(self):
        if self.pos < len(self.data):
            result = self.data[self.pos]
            self.pos += 1
            return result
        else:
            return 0

    def get_char(self): return self.get_number(1)

    def get_short(self): return self.get_number(2)

    def get_three(self): return self.get_number(3)

    def get_int(self): return self.get_number(4)

    def get_five(self): return self.get_number(5)

    def get_string(self, n):
        result = self.data[self.pos:self.pos+n]
        self.pos += n
        return result

    def get_break_string(self, break_byte=255):
        result = ""
        while self.pos < len(self.data) and self.data[self.pos] != break_byte:
            result += chr(self.data[self.pos])
            self.pos += 1
        self.pos += 1  # Skip past the break byte
        return result

    def next_chunk(self):
        while self.pos < len(self.data) and self.data[self.pos] != 255:
            self.pos += 1
        self.pos += 1  # Skip past the 0xFF byte

    def get_end_string(self):
        result = ""
        while self.pos < len(self.data):
            result += chr(self.data[self.pos])
            self.pos += 1
        return result

    def add_byte(self, x):
        if self.pos < len(self.data):
            self.data = self.data[:self.pos] + bytes([x]) + self.data[self.pos+1:]
        else:
            self.data += bytes([x])
        self.pos += 1
        return x

    def add_number(self, x, n):
        b = Packet.enumber(x, n)
        for i in range(n):
            self.add_byte(b[i])
        return x

    def add_char(self, x): return self.add_number(x, 1)

    def add_short(self, x): return self.add_number(x, 2)

    def add_three(self, x): return self.add_number(x, 3)

    def add_int(self, x): return self.add_number(x, 4)

    def add_five(self, x): return self.add_number(x, 5)

    def add_string(self, x):
        for c in x:
            self.add_byte(ord(c))
        return x

    def add_break_string(self, x):
        self.add_string(x)
        self.add_byte(255)
        return x
