 
from edge import Edge
import math

class Blitter():
    def __init__(self,frame) -> None:
        self.frame=frame
        pass

    def blitH(self,x,y,w):
        for i in range(math.floor(x),math.ceil(x+w)):
            self.frame[round(y),i,0]=1
            self.frame[round(y),i,1]=1
            self.frame[round(y),i,2]=1
        # print('draw s Line ',x,y,w)

def backward_insert_edge_based_on_x(edge) :
    x = edge.fX;
    prev = edge.fPrev;
    while (prev.fPrev and prev.fX > x) :
        prev = prev.fPrev;
    
    if (prev.fNext != edge) :
        remove_edge(edge);
        insert_edge_after(edge, prev)
        
def sort_edges(edges_list):
    edges_list.sort()
    l = len(edges_list)
    if l<1:
        return None,None
    for i in range(1,l+1) :
        if i< len(edges_list):
            edges_list[i - 1].fNext = edges_list[i]
            edges_list[i].fPrev = edges_list[i - 1]
    print('length===',len(edges_list),l)
    return edges_list[0],edges_list[l-1]

def backward_insert_start(prev,x):
    while (prev.fPrev and prev.fX > x) :
        prev = prev.fPrev
    return prev

def insert_edge_after(edge,afterMe):
    edge.fPrev = afterMe
    edge.fNext = afterMe.fNext
    afterMe.fNext.fPrev = edge
    afterMe.fNext = edge

def insert_new_edges(newEdge,curr_y):
    if (newEdge.fUpperY != curr_y) :
        return

    prev = newEdge.fPrev
    if (prev.fX <= newEdge.fX) :
        return

    #  find first x pos to insert
    start = backward_insert_start(prev, newEdge.fX)
    #  insert the lot, fixing up the links as we go
    while True:
        next = newEdge.fNext
        insetE = True
        while True:
            if (start.fNext == newEdge) :
                insetE=False
                break

            after = start.fNext
            if (after.fX >= newEdge.fX) :
                break

            start = after
        if insetE:
            remove_edge(newEdge)
            insert_edge_after(newEdge, start)

        start = newEdge
        newEdge = next
        if (newEdge.fUpperY != curr_y):
            break

def remove_edge(edge) :
    edge.fPrev.fNext = edge.fNext
    edge.fNext.fPrev = edge.fPrev


def walk_edges(blitter,prevHead,  start_y, stop_y,rightClip):
    print('walk_edges',start_y, stop_y)
    curr_y = start_y
    windingMask = 1
    left=0
    while(True):
        w = 0
        # left SK_INIT_TO_AVOID_WARNING
        currE = prevHead.fNext
        prevX = prevHead.fX
        eids=[]

        while (currE.fUpperY <= curr_y) :
            # print('currE',currE.id)
            x = currE.fX
            if ((w & windingMask) == 0) :
                left = x
                eids.append(currE.id)
        
            w += currE.fWinding
            if ((w & windingMask) == 0) :
                 width = x - left
                 if (width > 0) :
                    print('blitH-00000:',eids)
                    eids=[]
                    blitter.blitH(left, curr_y, width)
            next = currE.fNext
            newX = 0.0   

            if (currE.fLowerY == curr_y) :
                updateCurve = False
                if (currE.fCurveCount > 0) :
                    print('fCurveCount > 0')
                    if (currE.updateQuadratic()) :
                        newX = currE.fX
                        updateCurve=True
                    
                elif (currE.fCurveCount < 0) :
                    print('currE.fCurveCount < 0')
                    # if (currE.updateCubic()) :
                    #     newX = currE.fX
                    #     updateCurve=True  
                if updateCurve:
                   if (newX < prevX) :
                    backward_insert_edge_based_on_x(currE);
                   else :
                        prevX = newX
                else:        
                    remove_edge(currE)
            else : 
                newX = currE.fX + currE.fDX
                currE.fX = newX
                if (newX < prevX) :
                    backward_insert_edge_based_on_x(currE);
                else :
                    prevX = newX
                
             
            currE = next   
            eids.append(currE.id)

        if ((w & windingMask) != 0) :
            width = rightClip - left
            if (width > 0) :
               print('blitH-111:',eids)
               eids=[]
               blitter.blitH(left, curr_y, width)
              
        curr_y += 1
        if (curr_y >= stop_y):
            break
         
        insert_new_edges(currE, curr_y)         
    print('curr_y',curr_y)         

    

def fill_path(blitter,edges_list):
    edge,last = sort_edges(edges_list)
    if edge is None or last is None:
        return
    headEdge, tailEdge=Edge(),Edge()
    headEdge.fPrev = None
    headEdge.fNext = edge
    headEdge.fUpperY=0
    headEdge.fX =0
    edge.fPrev =headEdge

    last.fNext = tailEdge
    tailEdge.fPrev = last
    tailEdge.fUpperY = 1<<32

    start_y = 0
    stop_y = 800

    walk_edges(blitter,headEdge,  start_y, stop_y,0)