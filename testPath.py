'''
Author: wulong@yushu.biz wulong@yushu.biz
Date: 2023-04-19 20:55:29
LastEditors: wulong@yushu.biz wulong@yushu.biz
LastEditTime: 2023-04-19 22:52:43
FilePath: \ttfRender\testPath.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from path import Edge,Point 
from scan_path import fill_path,Blitter
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np

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

frame = np.zeros([800,800,3])
blitter = Blitter(frame)
fill_path(blitter,edges_list)
print('===============',frame.shape)
plt.title('hahahha')
plt.axis('off')
plt.imshow(frame)
plt.show()
