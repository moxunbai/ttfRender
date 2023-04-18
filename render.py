from fontTools.ttLib import TTFont
from fontTools.pens.freetypePen import FreeTypePen
from fontTools.misc.transform import Offset
import numpy as np
# import matplotlib.pyplot as plt
import taichi as ti

class Curve():

    def __init__(self) -> None:
        self.is_bezier=False
        self.points=[[0,0],[0,0],[0,0]]

vec2=ti.math.vec2


ti.init(arch=ti.gpu)

font = TTFont(r'Source_Han_Serif_CN_VF_Regular.ttf')

kv = font.keys()

# print(kv)

flags = list(font['glyf']['uni9EB8'].flags)
  

glyf_a=font['glyf']['uni9EB8']
# print(glyf_a.numberOfContours, glyf_a.endPtsOfContours)
# for attr,value in glyf_a.__dict__.items():
#     print(attr)
print('glyf_a',glyf_a.xMin,glyf_a.xMax,glyf_a.yMin,glyf_a.yMax)


word_w = glyf_a.xMax-glyf_a.xMin
word_h = glyf_a.yMax-glyf_a.yMin
word_min = vec2(glyf_a.xMin,glyf_a.yMin)
word_max = vec2(glyf_a.xMax,glyf_a.yMax)
coord = glyf_a.coordinates



def getContourPoints(fs,coords): 
    point_num = len(fs)
    pre_p = [0,0]
    curve_list=[]
    bezier_flag_list=[]
    if fs[0]==1:
        if fs[point_num-1]==1:
            pre_p[0] = (coords[0][0]+coords[point_num-1][0])/2
            pre_p[1] = (coords[0][1]+coords[point_num-1][1])/2
        else :
            pre_p = list(coords[point_num-1])
    for i in range(point_num) :
        p0_idx = i%point_num
        p1_idx = (i+1)%point_num
        p0_flag=fs[p0_idx]           
        p1_flag=fs[p1_idx]           
        p0=list(coords[p0_idx])           
        p1=list(coords[p1_idx])
        curve = Curve()
        if p0_flag == 1:
            curve.is_bezier=True
            curve.points[0]=pre_p
            curve.points[1]=p0
            if p1_flag == 1:
                curve.points[2]=[(p0[0]+p1[0])/2,(p0[1]+p1[1])/2]
                pre_p=curve.points[2]
            else:
                curve.points[2]=p1    
        elif p1_flag == 0:
            curve.points[0]=p0
            curve.points[1]=p1 
            pre_p = p0    
        else:
            p2_idx = (i+2)%point_num
            p2_flag = fs[p2_idx]
            p2 =list( coords[p2_idx])
            if p2_flag == 1:
                curve.is_bezier=True
                curve.points[0]=p0
                curve.points[1]=p1  
                curve.points[2]=[(p1[0]+p2[0])/2,(p1[1]+p2[1])/2]
                pre_p = curve.points[2]
            else:
                curve.points[0]=p0
                curve.points[1]=p1  
                curve.points[2]=p2
                pre_p = p0
        curve_list.append(curve.points)   
        bezier_flag_list.append(1 if curve.is_bezier else 0)   
    return curve_list,bezier_flag_list      


# @ti.func
def line_Bresenham_0(p0,p1,bitmap_field):
    p0,p1=ti.math.round(p0),ti.math.round(p1)
    v= p1-p0
    print(v)
    if v[0] == 0:
        for i in range(v[1]):
            bitmap_field[ti.math.round(p0[0]),i+ti.math.round(p0[1])]=1
    elif v[1]==0:
         for i in range(v[0]):
            bitmap_field[ti.math.round(p0[0])+i,ti.math.round(p0[1])]=1       
    else:
        k=v[1]/v[0]
        sl = ti.abs(k)>1
        x0= p0[1] if sl else p0[0]
        y0= p0[0] if sl else p0[1]
        x1= p1[1] if sl else p1[0]
        y1= p1[0] if sl else p1[1]
        dx =ti.abs(v[1] if sl else v[0] ) 
        x,y= x1,y1 
        if x0<=x1 :
            x,y=  x0,y0
        print('ppppp=',x,y,dx)
        p =  -dx  
        for i in range(ti.abs(dx)):
            if p>=0:
                p -=2*dx
                if sl:
                    x+=1 
                else:
                     y+=1 
            p+=2*dx 
            if sl:
              bitmap_field[y,x]=1 
              y+=1 
            else:   
                bitmap_field[x,y]=1
                x+=1    


# @ti.func
def line_Bresenham(p0,p1,bitmap_field):
    p0,p1=ti.math.round(p0),ti.math.round(p1)
    v= p1-p0
    dx = v[0]
    dy = v[1]
    dmx = dx
    dmy = dy
    m= ti.abs(dy/dx)
    xi = p0[0]
    yi = p0[1]
    if m>=1:
       dmx = dy
       dmy = dx 
    pi = 2*dmy - dmx
    while yi!=p1[1]+1:
        if pi <0:
            pi = pi+2*dmy
        else:
            pi = pi +2*dmy-2*dmx
            # yi += 1
            xi += 1
        bitmap_field[xi,yi]=1  
        # xi +=1
        yi +=1

def parse_contours(glyf_word):
    con_start=0
    for i in range(glyf_word.numberOfContours):
        con_end=glyf_a.endPtsOfContours[i]
        contour_coords = coord[con_start:con_end]
        contour_flags = flags[con_start:con_end]

        curve_list,bezier_flag_list  =getContourPoints(contour_flags,contour_coords)
        print(curve_list)
        break
        # cacl_contour_line( np.asarray(curve_list,dtype=np.float32) ,np.asarray(bezier_flag_list,dtype=np.float32) )


# parse_contours(glyf_a)

win_w=600
win_h=600
gui = ti.GUI('Hello World!', (win_w,win_h)) 
frame_np = np.zeros(shape=(win_w,win_h),dtype=np.float32)
frame_np_t = np.zeros(shape=(win_w,win_h,3),dtype=np.float32)
line_Bresenham(vec2(0,0),vec2(300,599),frame_np)

for i in range(win_w):
        for j in range(win_h):
            if i>30 and i<400 and i==j:
               frame_np_t[i,j]=[1,1,1]     
# X = np.random.random((5, 2))
# Y = np.random.random((5, 2))
while gui.running:
    # for i in range(len(coord)):
    #     c=coord[i]
    #     f=flags[i]
    #     if f == 1:
    #         x,y = (c[0]-glyf_a.xMin)/word_w/4,(c[1]-glyf_a.yMin)/word_h/4
    #         pos = [x+0.5,y+0.5]
    #         if x>1 or y>1:
    #             print(pos)
    #         gui.circle(pos)
    # for i in range(win_w):
    #     for j in range(win_h):
    #         if(frame_np[i,j]==1):
    #             #  print('llllllllllll',i,j)
    #              x,y = i/win_w,j/win_h
    #             #  pos = [x+0.5,y+0.5]
    #              pos = [x ,y ]
    #              gui.circle(pos,color=16777215, radius=1)
    gui.set_image(frame_np_t)
    # gui.lines(begin=X, end=Y, radius=1, color=0x068587)
    gui.show()