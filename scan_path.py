from path import Edge,Point 
import math

class Blitter():
    def __init__(self,frame) -> None:
        self.frame=frame
        pass

    def blitH(self,x,y,w):
        for i in range(math.floor(x),math.ceil(x+w)):
            self.frame[i,math.floor(x),0]=1
            self.frame[i,math.floor(x),1]=1
            self.frame[i,math.floor(x),2]=1
        print('draw s Line ',x,y,w)

def sort_edges(edges_list):
    edges_list.sort()
    l = len(edges_list)
    for i in range(1,l+1) :
        if i< len(edges_list):
            edges_list[i - 1].fNext = edges_list[i]
            edges_list[i].fPrev = edges_list[i - 1]
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
    print('walk_edges')
    curr_y = start_y
    windingMask = 1

    while(True):
        w = 0
        # left SK_INIT_TO_AVOID_WARNING
        currE = prevHead.fNext
        prevX = prevHead.fX

        while (currE.fUpperY <= curr_y) :
            x = currE.fX
            if ((w & windingMask) == 0) :
                left = x
        
            w += currE.fWinding
            if ((w & windingMask) == 0) :
                 width = x - left
                 if (width > 0) :
                    blitter.blitH(left, curr_y, width)
            next = currE.fNext
            newX = 0.0   

            if (currE.fLowerY == curr_y) :
                 
                remove_edge(currE)
            else : 
                newX = currE.fX + currE.fDX
                currE.fX = newX
             
            currE = next   

        if ((w & windingMask) != 0) :
            width = rightClip - left
            if (width > 0) :
               blitter.blitH(left, curr_y, width)
              
        curr_y += 1
        if (curr_y >= stop_y):
            break
         
        insert_new_edges(currE, curr_y)         
             

    

def fill_path(blitter,edges_list):
    edge,last = sort_edges(edges_list)
    headEdge, tailEdge=Edge(),Edge()
    print('edges_list: ', edge.fUpperY, edge.fX)
    headEdge.fPrev = None
    headEdge.fNext = edge
    headEdge.fUpperY=0
    headEdge.fX =0
    edge.fPrev =headEdge

    last.fNext = tailEdge
    tailEdge.fPrev = last
    tailEdge.fUpperY = 1<<32

    start_y = 0
    stop_y = 100

    walk_edges(blitter,headEdge,  start_y, stop_y,100)