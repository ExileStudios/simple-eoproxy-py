from enum import IntEnum

class OP(IntEnum):
    SECURITY = 1
    SYSTEM = 2
    LOGIN = 3
    ACCOUNT = 4
    CHARACTER = 5
    PLAY = 6
    DIR = 7
    MOVE = 8
    REST = 9
    SIT = 10
    ATTACK = 11
    MATTACK = 12
    MAGIC = 13
    PRIEST = 14
    UNK15 = 15
    TRADE = 16
    EFFECT = 17
    UNK18 = 18
    ITEM = 19
    UNK20 = 20
    EMOTE = 21
    CHAT = 22
    GLOBAL = 23
    UNK24 = 24
    UNK25 = 25
    GIFT = 26
    UNK27 = 27
    WARP = 28
    REFRESH = 29
    CHANNEL = 30
    NPC = 31
    RANGE = 32
    PLAYERRANGE = 33
    NPCRANGE = 34
    PLAYERS = 35
    PLAYER = 36
    GROUP = 37
    PAPERDOLL = 38
    TRADE2 = 39
    CHEST = 40
    SHOP = 41
    CHARGER = 42
    GATHER = 43
    FISHING = 44
    BANK = 45
    LOCKER = 46
    BARBER = 47
    TRANSPORT = 48
    GUILD = 49
    SOUND = 50
    JUKEBOX = 51
    GAMEBAR = 52
    MSGBOARD = 53
    CHARGER2 = 54
    ARENA = 56
    LAW = 57
    INN = 58
    BOSS = 59
    QUEST = 60
    GIFT2 = 61
    CAPTCHA = 249
    INIT = 255

class AC(IntEnum):
    REQUEST = 1
    RESULT = 2
    CONFIRM = 3
    TAKE = 6
    DO2 = 7
    RESULTOLD = 8
    DELETE = 9
    NEW = 10
    UPDATE = 11
    UNUSED8 = 12
    GET = 13
    SET = 14
    CREATE = 15
    ADD = 16
    DO = 17
    SWITCH = 18
    SELL = 19
    BUY = 20
    LIST = 21
    OPEN = 22
    CLOSE = 23
    CANCEL = 24
    SPAWN = 25
    PICKUP = 27
    UNK = 28
    DROP = 29
    JUNK = 30
    GROUP = 31
    PRIVATE = 33
    PUBLIC = 34
    PRIVATEOLD = 35
    PUBLICOLD = 36
    GLOBAL = 37
    SELF = 38
    TARGET = 39
    AREA = 40
    UNK43 = 43
    UNK44 = 44
    UNK45 = 45
    UNK46 = 46
    UNK47 = 47
    CONFIG = 230
    SYN1OLD = 231
    SYN1 = 241
    SYN2 = 242
    SYN3 = 243
    SYN4 = 244
    SYN5 = 245
    SYN6 = 246
    PING = 250
    PONG = 251
    NET3 = 252
    INIT = 255