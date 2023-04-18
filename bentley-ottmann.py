
s=[((15,17),(7,3)),((3,16),(6,10)),((2,15),(12,8)),((7,14),(11,6)),\
((10,13),(2,4)),((1,12),(9,5)),((-3,11),(5,2))]
points = [p  for edge in s for p in edge]
points = sorted(points,key = lambda a:  a[1],reverse=True)
print(s[1]) 
print(points)