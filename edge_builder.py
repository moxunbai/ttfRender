
import math
from path import Point,PathEdgeIter
from edge import Edge,QuadraticEdge

def is_not_monotonic(a,b,c):
    ab = a - b
    bc = b - c
    if (ab < 0) :
        bc = -bc
    return ab == 0 or bc < 0
def valid_unit_divide(  numer,   denom) :
    
    if (numer < 0) :
        numer = -numer
        denom = -denom
    

    if (denom == 0 or numer == 0 or numer >= denom) :
        return False,0
    

    r = numer / denom
    if (math.isnan(r)) :
        return False,0
    
    if (r == 0) :
        return False,0
     
    return True,r

def is_vertical(edge) :
    return edge.fDX == 0 and edge.fEdgeType == Edge.LINE_TYPE
def ChopQuadAt(src,dst,t):
    p0 = src[0]
    p1 = src[1]
    p2 = src[2]
    tt=t

    p01 = Point.interp(p0, p1, tt)
    p12 = Point.interp(p1, p2, tt)
    
    dst.append(p0)
    dst.append(p01)
    dst.append(Point.interp(p01, p12, tt))
    dst.append(p12)
    dst.append(p2)

def ChopQuadAtYExtrema(src,dst):
    a = src[0].y
    b = src[1].y
    c = src[2].y

    print('ChopQuadAtYExtrema abc',a,b,c)
    if (is_not_monotonic(a, b, c)) :
        print('ChopQuadAtYExtrema, is_not_monotonic',a,b,c)
        isOk,tValue=valid_unit_divide(a - b, a - b - b + c)
        if (isOk) :
            ChopQuadAt(src, dst, tValue)
            # flatten_double_quad_extrema(&dst[0].fY)
            return 1
        
        b = a if math.abs(a - b) < math.abs(b - c) else c
    
    dst[0].set(src[0].x, a)
    dst[1].set(src[1].x, b)
    dst[2].set(src[2].x, c)
    return 0

class EdgeBuilder():
    
    kNo_Combine=1
    kPartial_Combine=2
    kTotal_Combine=3
    
    
    def __init__(self,path):
        self.edgeList = []
        self.path=path
        
    def is_empty(self):
        return len(self.edgeList)==0
    
    def combineVertical(self,edge,last):
        if (last.fEdgeType != Edge.LINE_TYPE or last.fDX or edge.fX != last.fX):
            return EdgeBuilder.kNo_Combine
        if (edge.fWinding == last.fWinding) :
            if (edge.fLowerY + 1 == last.fUpperY) :
                last.fUpperY = edge.fUpperY
                return EdgeBuilder.kPartial_Combine

            if (edge.fUpperY == last.fLowerY + 1) :
                last.fLowerY = edge.fLowerY
                return EdgeBuilder.kPartial_Combine
            
            return EdgeBuilder.kNo_Combine
        
        if (edge.fUpperY == last.fUpperY) :
            if (edge.fLowerY == last.fLowerY) :
                return EdgeBuilder.kTotal_Combine
            
            if (edge.fLowerY < last.fLowerY) :
                last.fUpperY = edge.fLowerY + 1
                return EdgeBuilder.kPartial_Combine
            
            last.fUpperY = last.fLowerY + 1
            last.fLowerY = edge.fLowerY
            last.fWinding = edge.fWinding
            return EdgeBuilder.kPartial_Combine
        
        if (edge.fLowerY == last.fLowerY) :
            if (edge.fUpperY > last.fUpperY) :
                last.fLowerY = edge.fUpperY - 1
                return EdgeBuilder.kPartial_Combine
            
            last.fLowerY = last.fUpperY - 1
            last.fUpperY = edge.fUpperY
            last.fWinding = edge.fWinding
            return EdgeBuilder.kPartial_Combine
        
        return EdgeBuilder.kNo_Combine
    
    def addLine(self,pts):
        edge = Edge()
        # print('pts length',len(pts))
        if (edge.setLine(pts[0], pts[1])) :
            combine = self.combineVertical(edge, self.edgeList[-1]) if is_vertical(edge) and not self.is_empty() else EdgeBuilder.kNo_Combine
            # print('ccccc=====',combine)

            match combine:
                case EdgeBuilder.kTotal_Combine:    
                    self.edgeList.pop()
                case EdgeBuilder.kPartial_Combine: 
                    pass
                case EdgeBuilder.kNo_Combine:      
                    self.edgeList.append(edge)
            
            
    def buildEdges(self):
         
        iter = PathEdgeIter(self.path)
        e=iter.next()
        while e[0] is not None:
            pts,eType,isNewContour = e
            # print(eType, pts)
            match eType:
                case PathEdgeIter.kLine:
                    self.addLine(pts)
                case PathEdgeIter.kQuad: 
                    self.handle_quad(pts)
                # case PathEdgeIter.kConic: 
                #     quadPts = quadder.computeQuads(
                #                           pts, iter.conicWeight(), conicTol)
                #     for (int i = 0 i < quadder.countQuads() ++i) :
                #         handle_quad(quadPts)
                #         quadPts += 2
                # case PathEdgeIter.kCubic: 
                #     monoY[10]
                #     int n = SkChopCubicAtYExtrema(pts, monoY)
                #     for (int i = 0 i <= n i++) :
                #         self.addCubic(&monoY[i * 3])
                    
            e=iter.next()
        
        
    def handle_quad(self,pts):
        monoX=[Point(),Point(),Point()]
        for p in pts:
            print(p.x,p.y)
        n = ChopQuadAtYExtrema(pts, monoX)
        print('handle_quad',n)
        for  i in range(n+1) :
            start = i * 2
            end = start+3
            self.addQuad(monoX[start:end])
        
    def addQuad(self,pts):
        print('addQuad',len(pts))
        edge = QuadraticEdge()
        if edge.setQuadratic(pts):
           print('Quad Edge',edge) 
           self.edgeList.append(edge) 