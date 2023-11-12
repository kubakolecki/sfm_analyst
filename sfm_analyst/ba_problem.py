import geometry as geom
import numpy as np

class BaSettings:
    lossFunction = "NONE"
    lossFunctionParameter = 1.5
    noiseForImagePoints = 0.5
    noiseForControllPoints = {} #[collectionId [s_x s_y s_z ]]
    noiseForExternalOrientation = {} #[collectionId [s_x s_y s_z s_alpha s_beta s_gamma]]
    computeCorrelations = 0
    computeRedundancy = 0
    reportFileName = "report.txt"
    placeRaportInProjectDirecotry = True
    reportDirectory = ""
   
class BaProblem:
    def __init__(self,*, listOfObjectPointCollections, listOfImageCollections, baSettings ):
        self.imageCollections = listOfImageCollections
        self.objectPointsCollections =  listOfObjectPointCollections
        self.baSettings = baSettings
        print("len(self.objectPointsCollections): ",len(self.objectPointsCollections))
        self.imagePoints.clear()
        
        for objectPointCollection in  self.objectPointsCollections:
            objectPointCollection.clearImageIds()
        #generating object point observations, checking which object point is in the image
        for idOfImageCollection in range(0, len(self.imageCollections)):
            for idOfImage, image in self.imageCollections[idOfImageCollection].images.items():
                self.mapOfCameras[image.camera.name] = image.camera
                h = 0.5 * image.camera.height #for filtering image points
                w = 0.5 * image.camera.width #for filtering image points
                for objectPointCollection in self.objectPointsCollections:
                    imagePointsArray = geom.projectObjectPointCollectionToImage(image, objectPointCollection, 0, objectPointCollection.getNumberOfPoints() )
                    #checking if image points are in the range of the image
                    areWithinWidth = np.logical_and( imagePointsArray[0,:] < w, imagePointsArray[0,:] > -w)
                    areWithinHeight = np.logical_and( imagePointsArray[1,:] < h, imagePointsArray[1,:] > -h)
                    areInImage = np.logical_and(areWithinWidth, areWithinHeight)
                    indicesOfPointsInImage = np.where(areInImage)[1]
                    #creating image points
                    for i in indicesOfPointsInImage:
                        if objectPointCollection.ids[i] in objectPointCollection.pointIdsToNormalVectorMap:
                            normalVector = objectPointCollection.pointIdsToNormalVectorMap[objectPointCollection.ids[i]]
                            objectPointCoordinates = objectPointCollection.coordinates[0:3,i]
                            vectorFromPointToCamera = [image.pose.translation[0,0]-objectPointCoordinates[0],image.pose.translation[1,0]-objectPointCoordinates[1],image.pose.translation[2,0]-objectPointCoordinates[2]]
                            vectorFromPointToCamera /= np.linalg.norm(vectorFromPointToCamera)
                            cosinus = vectorFromPointToCamera[0]*normalVector[0] + vectorFromPointToCamera[1]*normalVector[1] + vectorFromPointToCamera[2]*normalVector[2]
                            if cosinus < 0.0:
                                continue

                        if objectPointCollection.ids[i] in objectPointCollection.pointIdsToVisibilityDistanceMap:
                            distanceThreshold = objectPointCollection.pointIdsToVisibilityDistanceMap[objectPointCollection.ids[i]]
                            vectorFromPointToCamera = [image.pose.translation[0,0]-objectPointCoordinates[0],image.pose.translation[1,0]-objectPointCoordinates[1],image.pose.translation[2,0]-objectPointCoordinates[2]]
                            distanceToPoint = np.linalg.norm(vectorFromPointToCamera)
                            if distanceToPoint > distanceThreshold:
                                continue

                        self.imagePoints.append(geom.ImagePoint(imagePointsArray[0,i],
                                                                imagePointsArray[1,i],
                                                                idOfImageCollection,
                                                                idOfImage,
                                                                objectPointCollection.collectionId,
                                                                objectPointCollection.ids[i]  ))
                        objectPointCollection.imagesIds[i].append((idOfImageCollection, idOfImage))
        self.__removeSingleRays()
        self.__buildMapOfImagePointsPerImage()

 

    def __removeSingleRays(self):
        print("number of image points before filtration: ", len(self.imagePoints) )
        validImagePoints = []
        for imagePoint in self.imagePoints:
            indexOfObjectPoint = self.objectPointsCollections[imagePoint.idOfObjectPointCollection].pointIdsToPositionMap[imagePoint.idOfObjectPoint] #.pointIdsToPositionMap[imagePoint.idOfObjectPoint]
            typeOfPoint = self.objectPointsCollections[imagePoint.idOfObjectPointCollection].types[indexOfObjectPoint]
            numberOfRays = len(self.objectPointsCollections[imagePoint.idOfObjectPointCollection].imagesIds[indexOfObjectPoint])
            if typeOfPoint == "tie" and numberOfRays > 1:
                validImagePoints.append(imagePoint)
                continue
            if typeOfPoint == "control" and numberOfRays > 0:
                validImagePoints.append(imagePoint)
                continue
            if typeOfPoint == "check" and numberOfRays > 1:
                validImagePoints.append(imagePoint)
                continue

        print("number of image points after filtration: ", len(validImagePoints) )      
        self.imagePoints = validImagePoints
    

    def __buildMapOfImagePointsPerImage(self):
        for i in range(0, len(self.imageCollections)):
            for imageId, image in self.imageCollections[i].images.items():
                id = str(i) + "_" + imageId
                self.imagePointsPerImage[id] = []
        
        for imagePoint in self.imagePoints:
            self.imagePointsPerImage[imagePoint.getCombinedImageName()].append(imagePoint)

    imageCollections = []
    objectPointsCollections = []
    imagePoints = []
    mapOfCameras = {}
    imagePointsPerImage = {}
    baSettings = BaSettings()