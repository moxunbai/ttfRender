from ctypes import c_int32,c_uint32,c_int64

Fixed1 = 1<<16
FixedHalf = 1<<15

INT32_MAX= 2147483647
INT32_MIN= -2147483648

def float_to_fixed(v):
    return int(v*Fixed1)
def int_to_fixed(v):
    return  v<<16

def fixed_to_float(v):
    return v* 1.52587890625e-5

def fixed_round_to_fixed( x) :
    return   c_int32(x + FixedHalf).value & 0xFFFF0000 
def fixed_ceil_to_fixed(x):
    return c_int32(x + Fixed1 - 1).value & 0xFFFF0000 
def fixed_floor_to_fixed(x):
    return c_int32(x).value & 0xFFFF0000 

def left_shift(x,shift):
    return c_int32(c_uint32(x).value << shift).value
def to_pin(x,lo,hi):
    return min(hi,max(x,lo))

def fixed_div(numer, denom): 
    v=to_pin((left_shift(c_int64(numer).value, 16) / (denom)), INT32_MIN, INT32_MAX)
    return c_int32(int(v)).value

def fixed_mul( a,  b) :
    return (c_int64(a).value * b >> 16)   

if __name__ == '__main__':
    print(Fixed1)
    print(65536/1024)
    a=float_to_fixed(1.22345)
    print(a)
    print(fixed_to_float(a))
    print(fixed_round_to_fixed(a))
    print(fixed_div(32,8),4<<16)
    print(fixed_mul(float_to_fixed(10),float_to_fixed(4)))
