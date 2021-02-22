import numpy as np
import geometry as geom

myObjectPoints = geom.ObjectPointCollection(collectionId = 1)
myObjectPoints.reserve(7)

myObjectPoints.insertPoint(0, 0, 0, 101, 0)
myObjectPoints.insertPoint(-12, 12, 0, 102, 1)
myObjectPoints.insertPoint(0, 12, 0, 103, 2)
myObjectPoints.insertPoint(12, 12, 0, 104, 3)
myObjectPoints.insertPoint(-12, -12, 0, 105, 4)
myObjectPoints.insertPoint(0, -12, 0, 106, 5)
myObjectPoints.insertPoint(12, -12, 0, 107, 6)

myCamera = geom.PinholeCamera(pixelSizeMilimeters=0.006, numberOfRows=6000, numberOfColumns=4000, principalDistanceMilimeters=20 )
myPose = geom.Pose()

translation = np.zeros((3,1))
translation[0,0] = 0.0
translation[1,0] = 0.0
translation[2,0] = 18.0

myPose.setTranslation(translation)
myPose.setRotationEuler(np.array([0.0,0.0,0.0]), "xyz")

myImage = geom.Image()
myImage.setPose(myPose)
myImage.setCamera(myCamera)

geom.projectImagePointCollectionToImage(myImage,myObjectPoints,0,7)

