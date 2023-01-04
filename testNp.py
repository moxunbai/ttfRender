import numpy as np


d = np.array([[1,2,3], [3,4,5,]])

c=d.repeat(3,axis=1).reshape(2,3,3)
print(c.shape)
print(c)
e=d[:,:,None]
print(e)

for x in np.nditer(c):
    print(x)