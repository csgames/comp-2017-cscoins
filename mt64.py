# Example of a Mersenne Twister MT-64 as used by the CSCoin.

def _int64(x):
    # Get the 64 least significant bits.
    return int(0xFFFFFFFFFFFFFFFF & x)

class MT64:
    w = 64
    n = 312
    m = 156
    r = 31
    a = 0xB5026F5AA96619E9
    u = 29
    d = 0x5555555555555555
    s = 17
    b = 0x71D67FFFEDA60000
    t = 37
    c = 0xFFF7EEE000000000
    l = 43
    f = 6364136223846793005

    lower_mask = 0x7FFFFFFF
    upper_mask = 0xffffffff80000000

    def __init__(self, seed):
        self.MT = [0] * MT64.n
        self.seed_mt(seed)


    def seed_mt(self, seed):
        self.index = MT64.n
        self.MT[0] = seed

        for i in range(1, MT64.n):
            self.MT[i] = _int64(MT64.f * (self.MT[i - 1] ^ (self.MT[i - 1] >> (MT64.w - 2))) + i)

    def extract_number(self):
        if self.index >= MT64.n:
            if (self.index > MT64.n):
                raise ValueError("Generator was never seeded")
            self.twist()

        y = self.MT[self.index]
        y = y ^ ((y >> MT64.u) & MT64.d)
        y = y ^ ((y << MT64.s) & MT64.b)
        y = y ^ ((y << MT64.t) & MT64.c)
        y = y ^ (y >> MT64.l)

        self.index += 1

        return y

    def twist(self):
        for i in range(MT64.n):
            x = (self.MT[i] & MT64.upper_mask) + (self.MT[(i + 1) % MT64.n] & MT64.lower_mask)
            xA = x >> 1

            if x % 2 != 0:
                xA = xA ^ MT64.a

            self.MT[i] = self.MT[(i + MT64.m) % MT64.n] ^ xA

        self.index = 0
