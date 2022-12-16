import numpy as np

xGrid, yGrid = np.meshgrid(range(0,5),range(0,5))

zGrid = np.ones((5,5))

gridData = np.dstack((yGrid,xGrid,zGrid))

listOfCoords = np.reshape(gridData,(5*5,3))



A = np.array([[0,1,2],[3,4,5],[6,7,8]])
B = np.reshape(A,(9,1))



Data = np.array([[4, 5.1, -2, -0.8, 1.3, -0.5, -0.7, 12.3],
                 [0.7, 6.1, 3.8, -0.8, 1.3, -0.5, 2.4, 17.3],
                 [6.1, 2.1, 2.8, 0.8, 2.2, 0.5, 1.4, 7.1]])

Data[np.where(Data<0.0)] = 0

print(Data)


x = Data[0,:]
y = Data[1,:]

selectedIds = np.logical_and(x <0, y>0 )
print(selectedIds)

E = Data[:,selectedIds ]

print(selectedIds.shape)
print(E)

print(Data)

negative = np.where(Data<0.0)


print(negative)