
from path import Path,Point
from edge import Edge,QuadraticEdge
from scan_path import fill_path,Blitter
from edge_builder import EdgeBuilder
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np

# p1 = Point(1,2)
# p2 = Point(20,40)
# p3 = Point(50,70)
# p4 = Point(70,110)
# p5 = Point(10,30)

# e1 = Edge()
# e1.setLine(p1,p2)
# e2 = Edge()
# e2.setLine(p2,p3)
# e3 = Edge()
# e3.setLine(p3,p4)
# e4 = Edge()
# e4.setLine(p4,p5)
# e5 = Edge()
# e5.setLine(p5,p1)

path = Path()
path.moveTo(1,2)
path.lineTo(100,250)
# path.lineTo(300,250)
path.quadTo(460,350,150,700)
# path.lineTo(250,550)
# path.lineTo(150,250)
path.lineTo(150,120)

builder = EdgeBuilder(path)
builder.buildEdges()
edges_list=builder.edgeList
for e in edges_list:
    print('edge:',e.fUpperY,e.fLowerY,e.fX,e.fY,e.fCurveCount)
# edges_list = [e1,e2,e3,e4,e5]

frame = np.zeros([800,800,3])
blitter = Blitter(frame)
fill_path(blitter,edges_list)
print('===============',frame.shape)
plt.title('hahahha')
plt.axis('off')
plt.imshow(frame)
plt.show()
