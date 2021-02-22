import numpy as np
import conversions as conv
import geometry
import sfmio

objectPoints = np.array([[30,0,100],[35,0,100]])
cameraMatrix = np.matrix([[5000,0,0],[0,5000,0],[0,0,1]])

projectionCenter1 = np.array([0.0, 0.0, 0.0])
projectionCenter2 = np.array([20.0, 0.0, 0.0]) 

projectionCenter1 = projectionCenter1[:,np.newaxis]
projectionCenter2 = projectionCenter2[:,np.newaxis]

pose1 = geometry.Pose()
pose2 = geometry.Pose()
camera1 = geometry.PinholeCamera(pixelSizeMilimeters=0.004, numberOfRows = 4000, numberOfColumns= 6000, principalDistanceMilimeters = 12.0)

pose1.setRotationEuler(conv.degrees2Radians(np.array([25.0,-3.0,-0.75])),'xyz')
pose1.setTranslation(projectionCenter1);

pose2.setRotationEuler(conv.degrees2Radians(np.array([0.0,-1.0,-0.55])),'xyz')
pose2.setTranslation(projectionCenter2);

print("getting transformation matrix for pose 1")
print(pose1.T)

print("getting transformation matrix for pose 2")
print(pose2.T)

image1 = geometry.Image()
image1.setCamera(camera1)
image1.setPose(pose1)

image2 = geometry.Image()
image2.setCamera(camera1)
image2.setPose(pose2)

collectionOfImages = geometry.ImageCollection()
collectionOfImages.addImage(image1,"im1")
collectionOfImages.addImage(image2,"im2")

sfmio.writeImageCollectionToObj(collectionOfImages,"test.obj")











