import sfmio
import geometry
import rasterio
import sgen
import ba_problem as ba
import numpy as np

AR = np.array([[3, 5, -1, 23, 11, 18, 0, 1],
         [-3, 19, 1, 5 , 11, 18, 4, -21],
        [1, 1, 1, 1, 1, 1, 1, 1]])

test1 = AR[0,:] < 10
test2 = AR[0,:] > -10
test3 = AR[1,:] < 10
test4 = AR[1,:] > -10

print(test1)
print(test2)
print(test3)
print(test4)

test = np.logical_and(np.logical_and(np.logical_and(test1, test2),test3),test4)
print(test)
trueidc = np.where(test)
print(trueidc)

for i in trueidc[0]:
    print(i)


flightMissionImages = geometry.ImageCollection()
missionCamera = geometry.PinholeCamera(pixelSizeMilimeters=0.004, numberOfRows = 4000, numberOfColumns= 6000, principalDistanceMilimeters = 20.0)

sfmio.importFromExternalOrientationTextfile("CaliforniaEO.txt",' ', flightMissionImages, "xyz", missionCamera )
sfmio.writeImageCollectionToObj(flightMissionImages, "test", imageWidthInMeters = 10, axesLenghtInMeters = 6.25)

#generating structure
dsm = rasterio.open("D:/DANE/tutorials/rasterio/opentopography/output_be.tif", driver="GTiff")

listOfImageCollections = []
listOfObjectPoints = []
listOfImageCollections.append(flightMissionImages)

structGenConfigTie = sgen.StructGenConfig(cellSize = 50.0, pointsPerCell = 1, dispersion = 1.5, approach = "uniform")
structGenConfigControll = sgen.StructGenConfig(cellSize = 85, pointsPerCell = 1, dispersion= 1.0, approach = "uniform", typeOfPoints= "controll")

imageRange = sgen.generateProcessingRangeFromImages(rasterioDsm = dsm, listOfImageCollections = listOfImageCollections)

objectPointsTie = sgen.generateUsingSurfaceModel(rasterioDsm = dsm,
                               givenRange = imageRange,
                               generationConfig = structGenConfigTie,
                               listOfImageCollections = listOfImageCollections,
                               id = 0)

objectPointsControll = sgen.generateUsingSurfaceModel(rasterioDsm = dsm,
                               givenRange = imageRange,
                               generationConfig = structGenConfigControll,
                               listOfImageCollections = listOfImageCollections,
                               id = 1)

listOfObjectPoints.append(objectPointsTie)
listOfObjectPoints.append(objectPointsControll)

sfmio.writeObjectPointsToFile("objectPointsTie.txt", objectPointsTie)
sfmio.writeObjectPointsToFile("objectPointsControll.txt", objectPointsControll)

#sfmio.writeSurfaceModelToObj("dsm.obj", dsm, imageRange)

print("len(listOfObjectPoints):", len(listOfObjectPoints))

#building ba problem
baProblem = ba.BaProblem(listOfObjectPointCollections = listOfObjectPoints, listOfImageCollections = listOfImageCollections, problemSettings = ba.ProblemSettings())
sfmio.writeRaysToDxf("rays_tie.dxf",baProblem,"tie",9)
sfmio.writeRaysToDxf("rays_controll.dxf",baProblem,"controll",1)