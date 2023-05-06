 
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
        
# 将边插入到最近的比它的x小的，或head位置
def backward_insert_edge_based_on_x(edge) :
    x = edge.fX
    prev = edge.fPrev
    while (prev.fPrev and prev.fX > x) :
        prev = prev.fPrev
    
    if (prev.fNext != edge) :
        remove_edge(edge)
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

# 往前找到最近的比x小的边直到head
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
    # 若边的上边界y 不等于当前扫描y return
    if (newEdge.fUpperY != curr_y) :
        return

    prev = newEdge.fPrev
    # 若上一个边的扫描x 小于等于当前x 返回
    if (prev.fX <= newEdge.fX) :
        return

    #  根据x找到第一个不比目标边x大的位置
    start = backward_insert_start(prev, newEdge.fX)
    #  insert the lot, fixing up the links as we go
    while True:
        next = newEdge.fNext
        insetE = True
        while True:
            # 若找到的边的下一位就是目标则不需要移动
            if (start.fNext == newEdge) :
                insetE=False
                break

            after = start.fNext
            # 若start的下一位大于等于目标边，就算找到正确位置
            if (after.fX >= newEdge.fX) :
                break

            start = after
        if insetE:
            # 把边从原位置处删除
            remove_edge(newEdge)
            # 然后插入到上面找到的边的后面
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

        while (currE.fUpperY <= curr_y) :
            # print('currE',currE.id)
            x = currE.fX
            # 之前是在区域外，x为新的左边界
            if ((w & windingMask) == 0) :
                left = x
        
            w += currE.fWinding
            # 当前边环绕数累加后是内部，则当前扫描线与当前边交点是有边界
            # 若左右边界有距离则渲染
            if ((w & windingMask) == 0) :
                 width = x - left
                 if (width > 0) :
                    blitter.blitH(left, curr_y, width)
            next = currE.fNext
            newX = 0.0   
            # 若当前边的下边界等于当前扫描线
            if (currE.fLowerY == curr_y) :
                updateCurve = False
                # 若当前边，曲线分段数大于0则认为是二次贝塞尔曲线
                if (currE.fCurveCount > 0) :
                    print('fCurveCount > 0')
                    # 若当前边更新过曲线成功，更新x为曲线的当前x
                    if (currE.updateQuadratic()) :
                        newX = currE.fX
                        updateCurve=True
                    
                elif (currE.fCurveCount < 0) :
                    print('currE.fCurveCount < 0')
                    # if (currE.updateCubic()) :
                    #     newX = currE.fX
                    #     updateCurve=True  
                # 若更新过曲线，且新的x小于之前的x ；则将此边提前；否则更新prevX
                if updateCurve:
                   if (newX < prevX) :
                    backward_insert_edge_based_on_x(currE)
                   else :
                        prevX = newX
                else:        
                    # 若没有更新曲线（表示曲线上所有分段折线扫描完了），或直线已扫描完毕
                    # 删除此边
                    remove_edge(currE)
            else : 
                # 若当前边还未被扫描完
                # 更新x
                newX = currE.fX + currE.fDX
                currE.fX = newX
                # 若新x小于前一个x，边位置提前
                # 否则记录prevX
                if (newX < prevX) :
                    backward_insert_edge_based_on_x(currE)
                else :
                    prevX = newX
                
            # 更新当前边为链表上下一个 
            currE = next
        # 若上面循环结束后，最后扫描到的边是又边界，需要渲染
        if ((w & windingMask) != 0) :
            width = rightClip - left
            if (width > 0) :
               blitter.blitH(left, curr_y, width)
        
        # y扫描线加一   
        curr_y += 1
        # 若到扫描下边界，跳出循环
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