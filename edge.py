import math
from ctypes import c_int32,c_uint32,c_int64
from dot6_util import float_to_dot6


# 计算非零位数
def CNZ(v):
    print(v,bin(v))
    c=0
    x=v
    while x>0:
        x=x>>1
        c+=1
    return c    
    
def cheap_distance( dx,  dy):
    dx = abs(dx)
    dy = abs(dy)
    if (dx > dy):
        dx += dy >> 1
    else:
        dx = dy + (dx >> 1)
    return dx


def diff_to_shift( dx,  dy,  shiftAA = 2):
    
    dist = cheap_distance(float_to_dot6(dx), float_to_dot6(dy))
    dist = (dist + (1 << 4)) >> (3 + shiftAA)
 
    return (CNZ(dist)) >> 1
class Edge( object ):
    
    MAX_COEFF_SHIFT = 6
    LINE_TYPE = 0
    QUAD_TYPE = 1
    def __init__(self) -> None:
        self.fPrev = None
        self.fNext = None

        self.fX = 0.0
        self.fDX = 0.0
        self.fY = 0.0
        self.fUpperY = 0
        self.fLowerY = 0
        self.fWinding = 0

    def __lt__(self,other):
       valuea = self.fUpperY
       valueb = other.fUpperY

       if (valuea == valueb) :
            valuea = self.fX
            valueb = other.fX

       return valuea < valueb

    def setLine(self,p0,p1):
        x0,x1,y0,y1 = p0.x,p1.x,p0.y,p1.y
        winding = 1

        if (y0 > y1) :
            x0, x1 = x1,x0
            y0, y1 =  y1,y0
             
            winding = -1
        top =  int(y0)
        bot =  int(y1)

        if (top == bot):
            return 0

        slope =  (x1 - x0)/(y1 - y0)
        dy = 1

        self.fX          = x0+slope*dy
        self.fDX         = slope
        self.fUpperY     = top
        self.fLowerY      = bot - 1
        self.fEdgeType   = Edge.LINE_TYPE
        self.fCurveCount = 0
        self.fWinding    = winding
        self.fCurveShift = 0
        return 1

 
 
class QuadraticEdge(Edge):
    
    def setQuadratic(self, pts,  shift=0) :
        if (self.setQuadraticWithoutUpdate(pts, shift)==0) :
            return 0
        return self.updateQuadratic()
    
    def setQuadraticWithoutUpdate(self,pts,shift):
        x0 = int(pts[0].x )
        y0 = int(pts[0].y )
        x1 = int(pts[1].x )
        y1 = int(pts[1].y )
        x2 = int(pts[2].x )
        y2 = int(pts[2].y )
 
        winding = 1
        if (y0 > y2):
            x0, x2 = x2, x0
            y0, y2 = y2, y0
            winding = -1

        top =  y0
        bot = y2
        print('setQuadraticWithoutUpdate',top == bot,x0,x1,x2,y0,y1,y2)
        if (top == bot):
            return 0
        dx = ( x1*2 - x0 - x2) >> 2
        dy = ( y1*2 - y0 - y2) >> 2
        
        shift = diff_to_shift(dx, dy, shift)
       
    
        if (shift == 0) :
            shift = 1
        elif(shift > Edge.MAX_COEFF_SHIFT) :
            shift = Edge.MAX_COEFF_SHIFT
        

        self.fWinding    =  winding
    
        self.fEdgeType   = Edge.QUAD_TYPE
        self.fCurveCount =  1 << shift 

        self.fCurveShift = shift - 1

        A = (x0 - x1 - x1 + x2)/2  
        B = x1 - x0             

        self.fQx     = x0
        self.fQDx    = B + (A* (1>> shift))     
        self.fQDDx   = A *(1>> (shift - 1))

        A = (y0 - y1 - y1 + y2)/2 
        B = (y1 - y0)

        self.fQy     = (y0)
        self.fQDy    = B + (A* (1>> shift)) 
        self.fQDDy   = A *(1>> (shift - 1))

        self.fQLastX = round(x2)
        self.fQLastY = round(y2)
        
    def updateQuadratic(self):
        success=0
        count = self.fCurveCount
        oldx = self.fQx
        oldy = self.fQy
        dx = self.fQDx
        dy = self.fQDy
        newx=0
        newy=0
        shift = self.fCurveShift
 
        while True:
            count -=1
            if (count > 0):
                newx    = oldx + (dx *(1>> shift))
                dx    += self.fQDDx
                newy    = oldy + (dy *(1>> shift))
                dy    += self.fQDDy
            
            else:
                newx    = self.fQLastX
                newy    = self.fQLastY
            
            success = self.updateLine(oldx, oldy, newx, newy)
            oldx = newx
            oldy = newy
            if count<1 or success:
                break
        

        self.fQx         = newx
        self.fQy         = newy
        self.fQDx        = dx
        self.fQDy        = dy
        self.fCurveCount = count
        return success
    
    def updateLine(self,x0, y0, x1, y1):
        top = round(y0)
        bot = round(y1)
 
        if (top == bot):
            return 0
 

        slope = (x1 - x0)/ (y1 - y0)
        dy  = top- y0
        self.fX          = x0 +  slope*dy
        self.fDX         = slope
        self.fUpperY     = top
        self.fLowerY      = bot - 1

        return 1