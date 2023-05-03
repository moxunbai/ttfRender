import math
from ctypes import c_int32,c_uint32,c_int64
from dot6_util import float_to_dot6

EdgeType = {'Line':1,'Quad':2,}

class Point( object ):
    
    @staticmethod
    def interp(p0,p1,t):
        x=p0.x+(p1.x-p0.x)*t
        y=p0.y+(p1.y-p0.y)*t
        return Point(x,y)
    
    def __init__(self,x=0.0,y=0.0) -> None:
        self.x=x
        self.y=y
    def set(self,x,y):
        self.x=x
        self.y=y  

class PathRef():
    
    def __init__(self) -> None:
        self.fPoints=[]
        self.fVerbs=[]
        self.fConicWeights=[]
        self.fSegmentMask=0
        pass
    
    def appendPoints(self,n):
        if n>0:
            for i in range(n):
                self.fPoints.append(Point())
            return   self.fPoints[len(self.fPoints)-n:]
    def points(self):
        return self.fPoints
    def growForVerb(self, verb, weight=1) :
        pCnt=0
        mask = 0
        match verb :
            case Path.kMove_Verb:
                pCnt = 1
            case Path.kLine_Verb:
                mask = Path.kLine_SegmentMask
                pCnt = 1
            case Path.kQuad_Verb:
                mask = Path.kQuad_SegmentMask
                pCnt = 2
            case Path.kConic_Verb:
                mask = Path.kConic_SegmentMask
                pCnt = 2
            case Path.kCubic_Verb:
                mask = Path.kCubic_SegmentMask
                pCnt = 3
            case Path.kClose_Verb:
                pCnt = 0
            case Path.kDone_Verb:
                pCnt = 0
            case _:
                pCnt = 0

        self.fSegmentMask |= mask
        self.fBoundsIsDirty = True 
        self.fIsOval = False
        self.fIsRRect = False

        self.fVerbs.append(verb)
        if (Path.kConic_Verb == verb) :
            self.fConicWeights.push_back(weight)
        pts = self.appendPoints(pCnt)
 
        return pts
    
    def countPoints(self):
        return len(self.fPoints)
    

class Path ():
    
    kMove_Verb=0
    kLine_Verb=1
    kQuad_Verb  = 2
    kConic_Verb = 3
    kCubic_Verb = 4
    kClose_Verb = 5
    kDone_Verb = 6
    
    kLine_SkPathSegmentMask   = 1 << 0
    kQuad_SkPathSegmentMask   = 1 << 1
    kConic_SkPathSegmentMask  = 1 << 2
    kCubic_SkPathSegmentMask  = 1 << 3
    
    kLine_SegmentMask  = kLine_SkPathSegmentMask
    kQuad_SegmentMask  = kQuad_SkPathSegmentMask
    kConic_SegmentMask = kConic_SkPathSegmentMask
    kCubic_SegmentMask = kCubic_SkPathSegmentMask
    
    def __init__(self):
        self.fPathRef = PathRef()
        self.fLastMoveToIndex=0
        pass
    
    def moveTo(self,x,y):
        self.fLastMoveToIndex = self.fPathRef.countPoints()
        pts =self.fPathRef.growForVerb(Path.kMove_Verb)
        pts[0].set(x, y)

        return 1
    
    def lineTo(self,x,y):
        # self.injectMoveToIfNeeded()
        pts = self.fPathRef.growForVerb(Path.kLine_Verb)
        pts[0].set(x, y)

    # return this->dirtyAfterEdit()
    
    def quadTo(self, x1,  y1,  x2,  y2) :
        # self.injectMoveToIfNeeded()
 
        pts =  self.fPathRef.growForVerb(Path.kQuad_Verb)
        pts[0].set(x1, y1)
        pts[1].set(x2, y2)
        
        
class PathEdgeIter():
      kLine  = Path.kLine_Verb
      kQuad  = Path.kQuad_Verb
      kConic = Path.kConic_Verb
      kCubic = Path.kCubic_Verb
      
      def __init__(self,  path) :
            print('init PathEdgeIter')
            self.fPts = path.fPathRef.points()
            self.fMoveToPtr = 0
            self.fVerbs = path.fPathRef.fVerbs
            self.fVerbsStop = len(path.fPathRef.fVerbs)
            self.fConicWeights = 0
            if (self.fConicWeights) :
                self.fConicWeights -= 1 

            self.fNeedsCloseLine = False
            self.fNextIsNewContour = False
            self.pointIdx=0
            self.verbIdx=0
            self.fScratch=[None,None]
            
      def closeline(self):
        self.fScratch[0] = self.fPts[len(self.fPts)-1]
        self.fScratch[1] = self.fPts[self.fMoveToPtr] 
        self.fNeedsCloseLine = False
        self.fNextIsNewContour = True
        return  (self.fScratch, Path.kLine_Verb, False )
      def next(self):
        while True:
            if (self.verbIdx == self.fVerbsStop) :
                return self.closeline()  if self.fNeedsCloseLine  else  ( None, -1, False )

            v = self.fVerbs[self.verbIdx]
            self.verbIdx+=1
            match (v) :
                case Path.kMove_Verb: 
                    if (self.fNeedsCloseLine) :
                        res = self.closeline()
                        self.fMoveToPtr = self.pointIdx
                        return res
                    
                    self.fMoveToPtr = self.pointIdx
                    self.pointIdx+=1
                    self.fNextIsNewContour = True
                case Path.kClose_Verb:
                    if (self.fNeedsCloseLine) :
                        return self.closeline()
                case _: 
                    pts_count = int( (v+2) / 2)
                    cws_count = int( (v & (v-1)) / 2)

                    self.fNeedsCloseLine = True
                    self.pointIdx           += pts_count
                    self.fConicWeights  += cws_count


                    isNewContour = self.fNextIsNewContour
                    self.fNextIsNewContour = False
                    s= self.pointIdx-pts_count-1
                    e= self.pointIdx
                    # print('next===',s,e,self.pointIdx ,v, pts_count,len(self.fPts))
                    return  (self.fPts[s:e], v, isNewContour )
                      
    