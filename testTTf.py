from fontTools.ttLib import TTFont
from fontTools.pens.freetypePen import FreeTypePen
from fontTools.misc.transform import Offset
import numpy as np
import matplotlib.pyplot as plt
import taichi as ti

vec2=ti.math.vec2

ti.init(arch=ti.gpu)
class Curve():

    def __init__(self) -> None:
        self.is_bezier=False
        self.points=[[0,0],[0,0],[0,0]]

# pen = FreeTypePen(None) # 实例化Pen子类
# font = TTFont(r'Alimama_ShuHeiTi_Bold.ttf')
font = TTFont(r'Source_Han_Serif_CN_VF_Regular.ttf')

kv = font.keys()

print(kv)
a=' '.encode('unicode_escape')
print(a,'\\uFF50'.encode().decode('unicode_escape'))
print('==============')
# for key,value in font.getBestCmap().items():
#     a=value.replace('uni','\\u')
#     b=a.encode().decode('unicode_escape')
#     # if(value == ' ' or b==' ' or value=='space'):
#     #     print('space',value,b)
#     # if('uni' not in value):
#     #     print('no uni:',value)    
#     print(key,":",value,b)

# for   n in font.getGlyphSet():
#     print(n)
# glyph = font.getGlyphSet()["uni9EB8"]
# glyph.draw(pen)

# width, ascender, descender = glyph.width, font['OS/2'].usWinAscent, -font['OS/2'].usWinDescent # 获取字形的宽度和上沿以及下沿
# height = ascender - descender # 利用上沿和下沿计算字形高度
# pen.show(width=width, height=height, transform=Offset(0, -descender)) # 显示以及矫正
# for g in glyph.glyphSet:
#     print(g)
# for attr,value in glyph.__dict__.items():
#     print(attr,value)
# print(font['glyf']['uni9EB8'].coordinates )   
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
coord = font['glyf']['uni9EB8'].coordinates
# for i in range(glyf_a.endPtsOfContours[0]):
#     print(coord[i],flags[i])

win_w=600
win_h=600
bitmap_field = ti.field(ti.i32)
fill_field = ti.field(ti.i32)
word_img_field = ti.Vector.field(n=3,dtype=ti.f32)
ti.root.dense(ti.ij, (win_w, win_h)).place(bitmap_field,fill_field,word_img_field)


#B = (1-t)*P0+t*P1
def one_bezier_curve(a, b, t):
    return (1-t)*a + t*b

#使用de Casteljau算法求解曲线
def n_bezier_curve(x, n, k, t):
    #当且仅当为一阶时，递归结束
    if n == 1:
        return one_bezier_curve(x[k], x[k+1], t)
    else:
        return (1-t)*n_bezier_curve(x, n-1, k, t) + t*n_bezier_curve(x, n-1, k+1, t)
 
def bezier_curve(x, y, num, b_x, b_y):
    #n表示阶数
    n = len(x) - 1
    t_step = 1.0 / (num - 1)
    t = np.arange(0.0, 1+t_step, t_step)
    for each in t:
        b_x.append(n_bezier_curve(x, n, 0, each))
        b_y.append(n_bezier_curve(y, n, 0, each))

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
            pre_p = coords[point_num-1]
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
# def getSlope(p0,p1)

@ti.func
def line_Bresenham(p0,p1):
    p0,p1=ti.math.round(p0),ti.math.round(p1)
    v= p1-p0
    if v[0] == 0:
        for i in range(v[1]):
            bitmap_field[ti.math.round(p0[0]),i+ti.math.round(p0[1])]=1
    elif v[1]==0:
         for i in range(v[0]):
            bitmap_field[ti.math.round(p0[0])+i,ti.math.round(p0[1])]=1       
    else:
        k=v[1]/v[0]
        sl = ti.math.abs(k)>1
        x0= p0[1] if sl else p0[0]
        y0= p0[0] if sl else p0[1]
        x1= p1[1] if sl else p1[0]
        y1= p1[0] if sl else p1[1]
        dx =ti.math.abs(v[1] if sl else v[0] ) 
        x,y= x1,y1 if x0>x1 else x0,y0

        p =  -dx  
        for i in range(ti.math.abs(dx)):
            if p>=0:
                p -=2*dx
                y+=1
            p+=2*dx
            if sl:
              bitmap_field[y,x]=1 
            else:   
                bitmap_field[x,y]=1




@ti.kernel
def cacl_contour_line(points_list:ti.types.ndarray(),types:ti.types.ndarray()):
    for i in range(types.shape[0]): 
        p0=vec2(points_list[i,0,0],points_list[i,0,1])-word_min
        p1=vec2(points_list[i,1,0],points_list[i,1,1])-word_min
        p2=vec2(points_list[i,2,0],points_list[i,2,1])-word_min
        t=types[i]
        if t == 0:
            line_Bresenham(p0,p1)
        else:

        print(points)


def parse_contours():
    con_start=0
    for i in range(glyf_a.numberOfContours):
        con_end=glyf_a.endPtsOfContours[i]
        contour_coords = coord[con_start:con_end]
        contour_flags = flags[con_start:con_end]

        curve_list,bezier_flag_list  =getContourPoints(contour_flags,contour_coords)
        cacl_contour_line( np.asarray(curve_list,dtype=np.float32) ,np.asarray(bezier_flag_list,dtype=np.float32) )

parse_contours()
# gui = ti.GUI('Hello World!', (600,600))
# indices = np.random.randint(0, 2, size=(50,))
# while gui.running:
#     for i in range(len(coord)):
#         c=coord[i]
#         f=flags[i]
#         if f == 1:
#             x,y = (c[0]-glyf_a.xMin)/word_w/4,(c[1]-glyf_a.yMin)/word_h/4
#             pos = [x+0.5,y+0.5]
#             if x>1 or y>1:
#                 print(pos)
#             gui.circle(pos)
#     gui.show()