import geometry as geom
import numpy as np

class ProblemSettings:
    estimatePrincipalDistance = False
    estimatePrincipalPoint = False
    estimateRaidalDistortion = False
    estimateTangentialDistortion = False

class BaProblem:
    def __init__(self,*, listOfObjectPointCollections, listOfImageCollections, problemSettings ):
        self.imageCollections = listOfImageCollections
        self.objectPointsCollections =  listOfObjectPointCollections
        print("len(self.objectPointsCollections): ",len(self.objectPointsCollections))
        self.imagePoints.clear()

        for objectPointCollection in  self.objectPointsCollections:
            objectPointCollection.clearImageIds()
        #generating object point observations, checking which object point is in the image
        for idOfImageCollection in range(0, len(self.imageCollections)):
            for idOfImage, image in self.imageCollections[idOfImageCollection].images.items():
                h = 0.5 * image.camera.height #for filtering image points
                w = 0.5 * image.camera.width #for filtering image points
                for objectPointCollection in self.objectPointsCollections:
                    imagePointsArray = geom.projectObjectPointCollectionToImage(image, objectPointCollection, 0, objectPointCollection.getNumberOfPoints() )
                    #checking if image points are in the range of the image
                    areWithinWidth = np.logical_and( imagePointsArray[0,:] < w, imagePointsArray[0,:] > -w)
                    areWithinHeight = np.logical_and( imagePointsArray[1,:] < h, imagePointsArray[1,:] > -h)
                    areInImage = np.logical_and(areWithinWidth, areWithinHeight)
                    indicesOfPointsInImage = np.where(areInImage)[1]
                    print("number of points from collection ",objectPointCollection.collectionId, " in image: ",idOfImageCollection, idOfImage," is: " , indicesOfPointsInImage.shape[0])
                    #creating image points
                    for i in indicesOfPointsInImage:
                        self.imagePoints.append(geom.ImagePoint(imagePointsArray[0,i],
                                                                imagePointsArray[1,i],
                                                                idOfImageCollection,
                                                                idOfImage,
                                                                objectPointCollection.collectionId,
                                                                objectPointCollection.ids[i]  ))
                        objectPointCollection.imagesIds[i].append((idOfImageCollection, idOfImage))
        self.removeSingleRays()



    def removeSingleRays(self):
        print("number of image points before filtration: ", len(self.imagePoints) )
        validImagePoints = []
        for imagePoint in self.imagePoints:
            indexOfObjectPoint = self.objectPointsCollections[imagePoint.idOfObjectPointCollection].pointIdsToPositionMap[imagePoint.idOfObjectPoint] #.pointIdsToPositionMap[imagePoint.idOfObjectPoint]
            typeOfPoint = self.objectPointsCollections[imagePoint.idOfObjectPointCollection].types[indexOfObjectPoint]
            numberOfRays = len(self.objectPointsCollections[imagePoint.idOfObjectPointCollection].imagesIds[indexOfObjectPoint])
            if typeOfPoint == "tie" and numberOfRays > 2:
                validImagePoints.append(imagePoint)
                continue
            if typeOfPoint == "controll" and numberOfRays > 0:
                validImagePoints.append(imagePoint)
                continue
            if typeOfPoint == "check" and numberOfRays > 1:
                validImagePoints.append(imagePoint)
                continue

        print("number of image points after filtration: ", len(validImagePoints) )      
        imagePoints = validImagePoints

    imageCollections = []
    objectPointsCollections = []
    imagePoints = []