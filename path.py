import math

class Point( object ):
    def __init__(self,x=0.0,y=0.0) -> None:
        self.x=x
        self.y=y
    def set(self,x,y):
        self.x=x
        self.y=y  
class Edge( object ):
    LINE_TYPE = 0
    def __init__(self) -> None:
        self.fPrev = None
        self.fNext = None

        self.fX = 0.0
        self.fDX = 0.0
        self.fY = 0.0
        self.fUpperY = 0.0
        self.fLowerY = 0.0
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
        top =  y0
        bot =  y1

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

 