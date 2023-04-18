from path import Edge,Point 


p1 = Point(1,2)
p2 = Point(2,4)
p3 = Point(5,7)
p4 = Point(13,2)
p5 = Point(6,5)

e1 = Edge()
e1.setLine(p1,p2)
e2 = Edge()
e2.setLine(p2,p3)
e3 = Edge()
e3.setLine(p3,p4)
e4 = Edge()
e4.setLine(p4,p5)

edges_list = [e1,e2,e3,e4]

def blitH(x,y,w):
    print('draw s Line ',x,y,w)

def sort_edges():
    edges_list.sort()
    l = len(edges_list)
    for i in range(1,l+1) :
        if i< len(edges_list):
            edges_list[i - 1].fNext = edges_list[i]
            edges_list[i].fPrev = edges_list[i - 1]
    return edges_list[0],edges_list[l-1]

def remove_edge(edge) :
    edge.fPrev.fNext = edge.fNext
    edge.fNext.fPrev = edge.fPrev

def walk_edges(prevHead,  start_y, stop_y):
    print('walk_edges')
    curr_y = start_y
    windingMask = 1

    while(True):
        w = 0
        # left SK_INIT_TO_AVOID_WARNING;
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
                    blitH(left, curr_y, width)
            next = currE.fNext
            newX = 0.0   

            if (currE.fLowerY == curr_y) :
                 
                remove_edge(currE)
            else : 
                newX = currE.fX + currE.fDX
                currE.fX = newX
             
            currE = next   

        if ((w & windingMask) != 0) :
            width = rightClip - left;
            if (width > 0) :
               blitH(left, curr_y, width);
              
        curr_y += 1
        if (curr_y >= stop_y):
            break;
         
        insert_new_edges(currE, curr_y);         
             

    

def fill_path():
    edge,last = sort_edges()
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

    walk_edges(headEdge,  start_y, stop_y)

fill_path()
