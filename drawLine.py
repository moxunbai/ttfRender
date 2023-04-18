
import numpy as np
# import matplotlib.pyplot as plt
import taichi as ti


ti.init(arch=ti.gpu)
I_Fixed1 = 1<<16

def scalarToFDot6(x):
    return x*64
def fDotFloor(x):
    return x>>6
def fDotCeil(x):
    return (x+63)>>6

def  fDotToFixed(x):
    return (x+32)>>6    

def smallDot6Scale(  value,   dot6) :
    return (value * dot6) >> 6

def fastfixdiv(  a,  b) :
    return  (a<<16) // b


def alphaMulInv256( value,  alpha256) : 
    prod = 0xFFFF - value * alpha256
    return (prod + (prod >> 8)) >> 8


# def getPackedA32(packed):
#     return (uint32_t)((packed) << (24 - SK_A32_SHIFT)) >> 24)
def getPackedR(packed):
    return (packed  >> 16)&0xFF
def getPackedG(packed):
    return (packed  >> 8)&0xFF
def getPackedB(packed):
    return (packed)&0xFF

def getPackedA32(packed):
    return packed & 0xFF

def blendARGB(  src,   dst,   aa) : 

    src_scale = aa+1
    dst_scale = alphaMulInv256(getPackedA32(src), src_scale)

    mask = 0xFF00FF
    nmask = 0xFF00FF00

    src_rb = (src & mask) * src_scale
    src_ag = ((src >> 8) & mask) * src_scale

    dst_rb = (dst & mask) * dst_scale
    dst_ag = ((dst >> 8) & mask) * dst_scale

    return (((src_rb + dst_rb) >> 8) & mask) | ((src_ag + dst_ag) & nmask)
  
def getFrameHexColor(x,y):
    [r,g,b]  = frame_np[x,y]
    r=int(r*255)
    g=int(g*255)
    b=int(b*255) 
    return (r<<16)|(g<<8)|b

def Splay( color) :
    mask = 0x00FF00FF
    return ((color >> 8) & mask),(color & mask)

def Unsplay(  ag,   rb) :
    mask = 0xFF00FF00
    return (ag & mask) | ((rb & mask) >> 8)    
def FastFourByteInterp256_32( src,  dst, scale) :
    # uint32_t src_ag, src_rb, dst_ag, dst_rb;
    src_ag, src_rb= Splay(src)
    dst_ag, dst_rb = Splay(dst)

    ret_ag = src_ag * scale + (256 - scale) * dst_ag
    ret_rb = src_rb * scale + (256 - scale) * dst_rb

    return Unsplay(ret_ag, ret_rb)

def blitAntiV2(x, y, a0, a1):
    
    oriColor0 = getFrameHexColor(x,y)
    # cv0 = blendARGB(0xffffffff,0xff000000|oriColor0,a0)
    cv0 = FastFourByteInterp256_32(0xffffffff,0x000000|oriColor0,a0)
    c = [getPackedR(cv0)/255,getPackedG(cv0)/255,getPackedB(cv0)/255]
    frame_np[x,y] = c
    oriColor1 = getFrameHexColor(x,y+1)
    # cv1 = blendARGB(0xffffffff,0xff000000|oriColor1,a1)
    cv1 = FastFourByteInterp256_32(0xffffffff,0x000000|oriColor1,a1)
    c = [getPackedR(cv1)/255,getPackedG(cv1)/255,getPackedB(cv1)/255]

    frame_np[x,y+1] =  c
    if x>536:
        print('blitAntiV2',a0, a1)
        # cc=getFrameHexColor(x,y)
        # print(hex(cc))
        # print(frame_np[x,y] ) 

def drawCap(x,   fy,   dy, mod64):
    print('drawCap')
    fy += I_Fixed1//2   
    lower_y = fy >> 16
    a = ((fy >> 8) & 0xFF)
    a0 = smallDot6Scale(255 - a, mod64)
    a1 = smallDot6Scale(a, mod64)
    blitAntiV2(x, lower_y - 1, a0, a1) 
    return fy + dy - I_Fixed1//2

def drawLine(x, stopx,   fy,   dy): 
    print('drawLine',x,stopx,   fy,   dy)
    fy += I_Fixed1//2
    while x <stopx:
        lower_y = fy >> 16
        a =  ((fy >> 8) & 0xFF)
        blitAntiV2(x, lower_y - 1, 255 - a, a)
        fy += dy
        x+=1

    return fy - I_Fixed1//2
def do_anti_hairline(x0,x1,y0,y1):
    scaleStart=0
    scaleStop=0
    istart=0
    istop=0
    fstart=0
    slope=0
    
    if ti.abs(x1-x0) >ti.abs(y1-y0):
        print('sdadasdasdasadasdadsadasda')
        if x0 > x1:
            x0,x1 = x1,x0
            y0,y1 = y1,y0
        istart = fDotFloor(x0)
        istop = fDotCeil(x1)
        fstart = fDotToFixed(y0) 

        if y0 == y1:
            slope =0 
            # todo huaheng
        else:
            slope = fastfixdiv(y1 - y0,x1 - x0) 
            print('slope: ', slope);
            fstart += (slope * (32 - (x0 & 63)) + 32) >> 6
            # hairBlitter = &horish_blitter     
        if  istop - istart == 1:
            scaleStart = x1 - x0
            scaleStop = 0
        else :
            scaleStart = 64 - (x0 & 63)
            scaleStop = x1 & 63
    fstart =  drawCap(istart, fstart, slope, scaleStart) 
    istart += 1
    fullSpans = istop - istart - (scaleStop > 0)
    print('fullSpans===',fullSpans,fstart)
    if (fullSpans > 0) :
        fstart = drawLine(istart, istart + fullSpans, fstart, slope)
     
    if (scaleStop > 0) :
        drawCap(istop - 1, fstart, slope, scaleStop)
    


win_w=600
win_h=600
gui = ti.GUI('Hello World!', (win_w,win_h)) 
frame_np = np.zeros(shape=(win_w,win_h,3),dtype=np.float32) 
# frame_np.fill(1)
x0 = scalarToFDot6(10)
x1 = scalarToFDot6(540)
y0 = scalarToFDot6(30)
y1 = scalarToFDot6(300)
do_anti_hairline(x0,x1,y0,y1)
# do_anti_hairline(x0,x1,y0,y1)
# ccc=blendARGB(0xffffffff,0,125)
# ccc=FastFourByteInterp256_32(0xffffffff,0,125)
# print(hex(ccc))
# print(hex(127))

# while gui.running: 
#     gui.set_image(frame_np)
    
#     gui.show()