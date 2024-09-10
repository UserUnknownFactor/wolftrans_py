seed = 0

RAND_MULTIPLIER = 0x343FD # LCG from msvcrt.dll
RAND_INCREMENT = 0x269EC3
RAND_MAX = 0x7FFF
MAX_INT32 = 0x7FFFFFFF
KC0 = 3000
KC1 = 20000
KC2 = 200

HAS_LIB = False
import ctypes, os
try:
    if os.name == "nt":
        libc = ctypes.CDLL("MSVCRT")
    else:
        libc = ctypes.CDLL("libc.so.6")
    HAS_LIB = True
except:
    pass

def get_seed():
    global seed
    return seed

def srand_my(s):
    global seed
    seed = s

def rand_my(mask: int = RAND_MAX):
    global seed
    seed = (seed * RAND_MULTIPLIER + RAND_INCREMENT) & MAX_INT32
    return (seed >> 16) & mask

srand = libc.srand if HAS_LIB else srand_my
rand = libc.rand if HAS_LIB else rand_my


# Constants
Nk = 4
Nb = 4
Nr = 10

AES_KEY_EXP_SIZE = 176
AES_KEY_SIZE = 16
AES_IV_SIZE = 16
AES_BLOCKLEN = 16

AES_ROUND_KEY_SIZE = AES_KEY_EXP_SIZE + AES_IV_SIZE

PW_SIZE = 15

# S-Box and Rcon
sbox = [
    0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76,
    0xCA, 0x82, 0xC9, 0x7D, 0xFA, 0x59, 0x47, 0xF0, 0xAD, 0xD4, 0xA2, 0xAF, 0x9C, 0xA4, 0x72, 0xC0,
    0xB7, 0xFD, 0x93, 0x26, 0x36, 0x3F, 0xF7, 0xCC, 0x34, 0xA5, 0xE5, 0xF1, 0x71, 0xD8, 0x31, 0x15,
    0x04, 0xC7, 0x23, 0xC3, 0x18, 0x96, 0x05, 0x9A, 0x07, 0x12, 0x80, 0xE2, 0xEB, 0x27, 0xB2, 0x75,
    0x09, 0x83, 0x2C, 0x1A, 0x1B, 0x6E, 0x5A, 0xA0, 0x52, 0x3B, 0xD6, 0xB3, 0x29, 0xE3, 0x2F, 0x84,
    0x53, 0xD1, 0x00, 0xED, 0x20, 0xFC, 0xB1, 0x5B, 0x6A, 0xCB, 0xBE, 0x39, 0x4A, 0x4C, 0x58, 0xCF,
    0xD0, 0xEF, 0xAA, 0xFB, 0x43, 0x4D, 0x33, 0x85, 0x45, 0xF9, 0x02, 0x7F, 0x50, 0x3C, 0x9F, 0xA8,
    0x51, 0xA3, 0x40, 0x8F, 0x92, 0x9D, 0x38, 0xF5, 0xBC, 0xB6, 0xDA, 0x21, 0x10, 0xFF, 0xF3, 0xD2,
    0xCD, 0x0C, 0x13, 0xEC, 0x5F, 0x97, 0x44, 0x17, 0xC4, 0xA7, 0x7E, 0x3D, 0x64, 0x5D, 0x19, 0x73,
    0x60, 0x81, 0x4F, 0xDC, 0x22, 0x2A, 0x90, 0x88, 0x46, 0xEE, 0xB8, 0x14, 0xDE, 0x5E, 0x0B, 0xDB,
    0xE0, 0x32, 0x3A, 0x0A, 0x49, 0x06, 0x24, 0x5C, 0xC2, 0xD3, 0xAC, 0x62, 0x91, 0x95, 0xE4, 0x79,
    0xE7, 0xC8, 0x37, 0x6D, 0x8D, 0xD5, 0x4E, 0xA9, 0x6C, 0x56, 0xF4, 0xEA, 0x65, 0x7A, 0xAE, 0x08,
    0xBA, 0x78, 0x25, 0x2E, 0x1C, 0xA6, 0xB4, 0xC6, 0xE8, 0xDD, 0x74, 0x1F, 0x4B, 0xBD, 0x8B, 0x8A,
    0x70, 0x3E, 0xB5, 0x66, 0x48, 0x03, 0xF6, 0x0E, 0x61, 0x35, 0x57, 0xB9, 0x86, 0xC1, 0x1D, 0x9E,
    0xE1, 0xF8, 0x98, 0x11, 0x69, 0xD9, 0x8E, 0x94, 0x9B, 0x1E, 0x87, 0xE9, 0xCE, 0x55, 0x28, 0xDF,
    0x8C, 0xA1, 0x89, 0x0D, 0xBF, 0xE6, 0x42, 0x68, 0x41, 0x99, 0x2D, 0x0F, 0xB0, 0x54, 0xBB, 0x16
]

Rcon = [0x8D, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36]

def keyExpansion(pRoundKey, pKey):
    tempa = [0, 0, 0, 0]

    # The first round key is the key itself.
    for i in range(Nk):
        pRoundKey[i * 4 + 0] = pKey[i * 4 + 0]
        pRoundKey[i * 4 + 1] = pKey[i * 4 + 1]
        pRoundKey[i * 4 + 2] = pKey[i * 4 + 2]
        pRoundKey[i * 4 + 3] = pKey[i * 4 + 3]

    for i in range(Nk, Nb * (Nr + 1)):
        k = (i - 1) * 4
        tempa[0] = pRoundKey[k + 0]
        tempa[1] = pRoundKey[k + 1]
        tempa[2] = pRoundKey[k + 2]
        tempa[3] = pRoundKey[k + 3]

        if (i % Nk) == 0:
            u8tmp = tempa[0]
            tempa[0] = tempa[1]
            tempa[1] = tempa[2]
            tempa[2] = tempa[3]
            tempa[3] = u8tmp

            tempa[0] = sbox[tempa[0]] ^ Rcon[i // Nk]
            tempa[1] = sbox[tempa[1]] >> 4
            tempa[2] = ~sbox[tempa[2]]
            tempa[3] = (sbox[tempa[3]] >> 7) | (sbox[tempa[3]] << 1)

        j = i * 4
        k = (i - Nk) * 4

        pRoundKey[j + 0] = pRoundKey[k + 0] ^ tempa[0]
        pRoundKey[j + 1] = pRoundKey[k + 1] ^ tempa[1]
        pRoundKey[j + 2] = pRoundKey[k + 2] ^ tempa[2]
        pRoundKey[j + 3] = pRoundKey[k + 3] ^ tempa[3]


def addRoundKey(pState, round, pRoundKey):
    for i in range(AES_KEY_SIZE):
        pState[i] ^= pRoundKey[round * AES_KEY_SIZE + i]


def subBytes(pState):
    for i in range(AES_KEY_SIZE):
        pState[i] = sbox[pState[i]]


def shiftRows(pState):
    temp = pState[1]
    pState[1] = pState[5]
    pState[5] = pState[9]
    pState[9] = pState[13]
    pState[13] = temp

    temp = pState[2]
    pState[2] = pState[10]
    pState[10] = temp

    temp = pState[6]
    pState[6] = pState[14]
    pState[14] = temp

    temp = pState[3]
    pState[3] = pState[15]
    pState[15] = pState[11]
    pState[11] = pState[7]
    pState[7] = temp

def xtime(x):
    return ((x << 1) ^ (((x >> 7) & 1) * 0x1b))

def mixColumns(pState):
    tmp = 0
    t = 0

    for i in range(4):
        t = pState[0]
        tmp = pState[1] ^ pState[0] ^ pState[2] ^ pState[3]

        pState[0] ^= tmp ^ xtime(pState[1] ^ pState[0])
        pState[1] ^= tmp ^ xtime(pState[2] ^ pState[1])
        pState[2] ^= tmp ^ xtime(pState[2] ^ pState[3])
        pState[3] ^= tmp ^ xtime(pState[3] ^ t)

        pState = pState[4:]


# AES Cipher
def cipher(pState, pRoundKey):
    addRoundKey(pState, 0, pRoundKey)

    for round in range(1, Nr):
        subBytes(pState)
        shiftRows(pState)
        mixColumns(pState)
        addRoundKey(pState, round, pRoundKey)

    subBytes(pState)
    shiftRows(pState)
    addRoundKey(pState, Nr, pRoundKey)


# AES_CTR_xcrypt
def aesCtrXCrypt(pData, pKey, size):
    state = [0] * AES_BLOCKLEN
    pIv = pKey[AES_KEY_EXP_SIZE:]
    bi = AES_BLOCKLEN

    for i in range(size):
        bi += 1
        if bi == AES_BLOCKLEN:
            state[:] = pIv[:]
            cipher(state, pKey)

            for j in range(AES_BLOCKLEN - 1, -1, -1):
                if pIv[j] == 0xFF:
                    pIv[j] = 0
                    continue
                pIv[j] += 1
                break
            bi = 0

        pData[i] ^= state[bi]


class CryptData:
    def __init__(self):
        self.keyBytes = [0] * 4
        self.seedBytes = [0] * 4
        self.gameDatBytes = []
        self.dataSize = 0
        self.seed1 = 0
        self.seed2 = 0


class RngData:
    OUTER_VEC_LEN = 0x20
    INNER_VEC_LEN = 0x100
    DATA_VEC_LEN = 0x30

    def __init__(self):
        self.seed1 = 0
        self.seed2 = 0
        self.counter = 0
        self.data = [[0] * INNER_VEC_LEN for _ in range(OUTER_VEC_LEN)]

    def Reset(self):
        self.seed1 = 0
        self.seed2 = 0
        self.counter = 0
        self.data = [[0] * RngData.INNER_VEC_LEN for _ in range(RngData.OUTER_VEC_LEN)]


def customRng1(rd):
    state = 0
    stateMod = 0

    seedP1 = (rd.seed1 ^ (((rd.seed1 << 11) ^ rd.seed1) >> 8))
    seed = (rd.seed1 << 11) ^ seedP1

    state = 1664525 * seed + 1013904223

    if ((13 * seedP1 + 95) & 1) == 0:
        stateMod = state // 8
    else:
        stateMod = state * 4

    state ^= stateMod

    if (state & 0x400) != 0:
        state ^= state << 21
        stateMod = state >> 9
    else:
        state ^= state * 4
        stateMod = state >> 22

    state ^= stateMod

    if (state & 0xFFFFF) == 0:
        state += 256

    rd.seed1 = state
    return state


def customRng2(rd):
    stateMod = 0
    state = 0

    seed = rd.seed1

    state = 1664525 * seed + 1013904223
    stateMod = (seed & 7) + 1

    if state % 3:
        if state % 3 == 1:
            state ^= (state >> stateMod)
        else:
            state = ~state + (state << stateMod)
    else:
        state ^= (state << stateMod)

    if state:
        if not state & 0xFFFF:
            state ^= 0x55AA55AA
    else:
        state = 0x173BEF

    rd.seed1 = state
    return state


def customRng3(rd):
    state = 0
    seed = rd.seed2

    state = (1566083941 * rd.seed2) ^ (292331520 * rd.seed2)
    state ^= (state >> 17) ^ (32 * (state ^ (state >> 17)))
    state = 69069 * (state ^ (state ^ (state >> 11)) & 0x3FFFFFFF)

    if state:
        if not state & 0xFFFF:
            state ^= 0x59A6F141

        if (state & 0xFFFFF) == 0:
            state += 256
    else:
        state = 1566083941

    rd.seed2 = state
    return state


def rngChain(rd, data):
    for i, d in enumerate(data):
        rn = customRng2(rd)

        d = rn ^ customRng3(rd)

        if (rd.counter + 1) & 1 == 0:
            d += customRng3(rd)

        if not (rd.counter % 3):
            d ^= customRng1(rd) + 3

        if not (rd.counter % 7):
            d += customRng3(rd) + 1

        if (rd.counter & 7) == 0:
            d *= customRng1(rd)

        if not ((i + rd.seed1) % 5):
            d ^= customRng1(rd)

        if not (rd.counter % 9):
            d += customRng2(rd) + 4

        if not (rd.counter % 0x18):
            d += customRng2(rd) + 7

        if not (rd.counter % 0x1F):
            d += 3 * customRng3(rd)

        if not (rd.counter % 0x3D):
            d += customRng3(rd) + 1

        if not (rd.counter % 0xA1):
            d += customRng2(rd)

        if rn & 0xFFFF == 256:
            d += 3 * customRng3(rd)

        rd.counter += 1


def runCrypt(rd, seed1, seed2):
    rd.seed1 = seed1
    rd.seed2 = seed2
    rd.counter = 0

    srand(seed1)

    for i in range(rd.data.size()):
        rngChain(rd, rd.data[i])


def aLotOfRngStuff(rd, a2, a3, idx, cryptData):
    itrs = 20

    for i in range(itrs):
        idx1 = (a2 ^ customRng1(rd)) & 0x1F
        idx2 = (a3 ^ customRng2(rd)) & 0xFF
        a3 = rd.data[idx1][idx2]

        switch_val = (a2 + rd.counter) % 0x14
        if switch_val == 1:
            rngChain(rd, rd.data[(a2 + 5) & 0x1F])
        elif switch_val == 2:
            a3 ^= customRng1(rd)
        elif switch_val == 5:
            if a2 & 0xFFFFF == 0:
                cryptData[idx] ^= customRng3(rd)
        elif switch_val == 9 or switch_val == 0xE:
            cryptData[customRng2(rd) % 0x30] += a3
        elif switch_val == 0xB:
            cryptData[idx] ^= customRng1(rd)
        elif switch_val == 0x11:
            itrs += 1
        elif switch_val == 0x13:
            if a2 & 0xFFFF == 0:
                cryptData[idx] ^= customRng2(rd)

        a2 += customRng3(rd)

        if itrs > 50:
            itrs = 50

    cryptData[idx] += a3


def aesKeyGen(cd, rd, aesKey, aesIv):
    runCrypt(rd, cd.seedBytes[0], cd.seedBytes[1])

    cryptData = [0] * RngData.DATA_VEC_LEN

    for i in range(RngData.DATA_VEC_LEN):
        aLotOfRngStuff(rd, i + cd.seedBytes[3], cd.seedBytes[2] - i, i, cryptData)

    seed = cd.seedBytes[1] ^ cd.seedBytes[2]

    srand(seed)

    indexes = list(range(RngData.DATA_VEC_LEN))
    resData = [0] * RngData.DATA_VEC_LEN

    for i in range(RngData.DATA_VEC_LEN):
        rn = rand(0xFFFF) % RngData.DATA_VEC_LEN
        old = indexes[i]
        indexes[i] = indexes[rn]
        indexes[rn] = old

    for i in range(RngData.DATA_VEC_LEN):
        resData[i] = cryptData[indexes[i]]

    aesKey[:] = resData[:AES_KEY_SIZE]
    aesIv[:] = resData[AES_KEY_SIZE:AES_KEY_SIZE + AES_IV_SIZE]


def genMTSeed(seeds):
    seedP1 = (seeds[1] | (seeds[0] << 8)) << 8
    seedP2 = ((((seeds[2] | seedP1) << 13) ^ (seeds[2] | seedP1)) >> 17) ^ ((seeds[2] | seedP1) << 13) ^ (seeds[2] | seedP1)
    seed = (32 * seedP2) ^ seedP2

    return seed

class mt19937():
    u, d = 11, 0xFFFFFFFF
    s, b = 7, 0x9D2C5680
    t, c = 15, 0xEFC60000
    l = 18
    n = 624

    def to_int32(self, x):
        return(x & 0xFFFFFFFF)

    def __init__(self, seed):
        w = 32
        r = 31
        f = 1812433253
        self.m = 397
        self.a = 0x9908B0DF
        self.MT = [0] * self.n
        self.index = self.n + 1
        self.lower_mask = (1 << r) - 1
        self.upper_mask = self.to_int32(~self.lower_mask)
        self.MT[0] = self.to_int32(seed)
        for i in range(1, self.n):
            self.MT[i] = self.to_int32((f * (self.MT[i - 1] ^ (self.MT[i - 1] >> (w - 2))) + i))

    def rand(self, mask=None):
        if self.index >= self.n:
            self.twist()
            self.index = 0
        y = self.MT[self.index]

        y = y ^ ((y >> self.u) & self.d)
        y = y ^ ((y << self.s) & self.b)
        y = y ^ ((y << self.t) & self.c)
        y = y ^ (y >> self.l)
        self.index += 1
        return y & mask if mask is not None else self.to_int32(y)

    def twist(self):
        for i in range(0, self.n):
            x = (self.MT[i] & self.upper_mask) + (self.MT[(i + 1) % self.n] & self.lower_mask)
            xA = x >> 1
            if(x % 2) != 0:
                xA = xA ^ self.a
            self.MT[i] = self.MT[(i + self.m) % self.n] ^ xA


def untemper(y):
    y ^= y >> mt19937.l
    y ^= y << mt19937.t & mt19937.c
    for i in range(7):
        y ^= y << mt19937.s & mt19937.b
    for i in range(3):
        y ^= y >> mt19937.u & mt19937.d
    return y

def decrpytProV2P1(data, seed):
    NUM_RNDS = 128
    myrng = mt19937(seed)
    rnds = [myrng.rand(0xFF) for _ in range(NUM_RNDS)]

    for i in range(0xA, len(data)):
        data[i] ^= rnds[i % NUM_RNDS]


def initCryptProt(cd):
    fileSize = len(cd.gameDatBytes)

    if fileSize - 20 < 326:
        cd.dataSize = fileSize - 20
    else:
        cd.dataSize = 326

    decrpytProV2P1(cd.gameDatBytes, genMTSeed([cd.gameDatBytes[0], cd.gameDatBytes[3], cd.gameDatBytes[9]]))

    cd.keyBytes[:] = cd.gameDatBytes[0xB:0xF]

    cd.seedBytes[0] = cd.gameDatBytes[7] + 3 * cd.keyBytes[0]
    cd.seedBytes[1] = cd.keyBytes[1] ^ cd.keyBytes[2]
    cd.seedBytes[2] = cd.keyBytes[3] ^ cd.gameDatBytes[7]
    cd.seedBytes[3] = cd.keyBytes[2] + cd.gameDatBytes[7] - cd.keyBytes[0]

    cd.seed1 = cd.keyBytes[1] ^ cd.keyBytes[2]
    cd.seed2 = cd.keyBytes[1] ^ cd.keyBytes[2]


def decrypt_dat_v2(data):
    cd = CryptData()
    rd = RngData()

    cd.gameDatBytes = data
    initCryptProt(cd)

    runCrypt(rd, cd.seed1, cd.seed2)

    aesKey = [0] * AES_KEY_SIZE
    aesIv = [0] * AES_IV_SIZE
    aesKeyGen(cd, rd, aesKey, aesIv)

    roundKey = [0] * AES_ROUND_KEY_SIZE
    keyExpansion(roundKey, aesKey)
    roundKey[AES_KEY_EXP_SIZE:] = aesIv[:]

    aesCtrXCrypt(cd.gameDatBytes[20:], roundKey, cd.dataSize)
    return cd.gameDatBytes

def decrypt_dat_v1(data, seeds, intervals):
    for i, seed in enumerate(seeds):
        srand(seed)
        for j in range(0, len(data), intervals[i]):
            data[j] ^= (rand(0xFFFF) >> 12) & 0xFF

    return data

def decrypt_proj(data, s_proj_key):
    srand(s_proj_key)
    return bytearray([byte ^ rand(0xFF) for byte in data])
