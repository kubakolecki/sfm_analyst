import sfmio
import xtrelio
import geometry
import rasterio
import sgen
import ba_problem as ba
import numpy as np

flightMissionImages = geometry.ImageCollection(collectionId = 0)
missionCamera = geometry.PinholeCamera(name = "myCamera" , pixelSizeMilimeters=0.004, numberOfRows = 4000, numberOfColumns= 6000, principalDistanceMilimeters = 20.0)
baSettings = xtrelio.readBaSettings("baconfig.yaml")
outputXtrelDirectoryName = "CaliforniaSmall"
sfmio.importFromExternalOrientationTextfile("CaliforniaSmallEO.txt",' ',
                                           flightMissionImages,
                                           "xyz",
                                           observedPosition = False,
                                           observedOrientation = False,
                                           camera = missionCamera )
sfmio.writeImageCollectionToObj(flightMissionImages, "test", imageWidthInMeters = 12, axesLenghtInMeters = 7.0)

#generating structure
dsm = rasterio.open("D:/DANE/tutorials/rasterio/opentopography/output_be.tif", driver="GTiff")

listOfImageCollections = []
listOfImageCollections.append(flightMissionImages)

stdDevControllPoints = np.array([baSettings.noiseForControllPoints[1][0], baSettings.noiseForControllPoints[1][1], baSettings.noiseForControllPoints[1][2] ])

structGenConfigTie = sgen.StructGenConfig(cellSize = 65, pointsPerCell = 2, dispersion = 1.5, approach = "uniform")
structGenConfigControll = sgen.StructGenConfig(cellSize = 65, pointsPerCell = 1, dispersion= 1.0, standardDeviation = stdDevControllPoints, approach = "uniform", typeOfPoints= "controll")
structGenConfigCheck = sgen.StructGenConfig(cellSize = 100, pointsPerCell = 1, dispersion= 1.0, approach = "uniform", typeOfPoints= "check")

imageRange = sgen.generateProcessingRangeFromImages(rasterioDsm = dsm, listOfImageCollections = listOfImageCollections)

objectPointsTie = sgen.generateUsingSurfaceModel(rasterioDsm = dsm,
                               givenRange = imageRange,
                               generationConfig = structGenConfigTie,
                               id = 0)

objectPointsControll = sgen.generateUsingSurfaceModel(rasterioDsm = dsm,
                               givenRange = imageRange,
                               generationConfig = structGenConfigControll,
                               id = 1)

objectPointsCheck = sgen.generateUsingSurfaceModel(rasterioDsm = dsm,
                               givenRange = imageRange,
                               generationConfig = structGenConfigCheck,
                               id = 2)

listOfObjectPoints = [objectPointsTie, objectPointsControll, objectPointsCheck]

sfmio.writeObjectPointsToFile("objectPointsTie.txt", objectPointsTie)
sfmio.writeObjectPointsToFile("objectPointsControll.txt", objectPointsControll)

#sfmio.writeSurfaceModelToObj("dsm.obj", dsm, imageRange)

print("len(listOfObjectPoints):", len(listOfObjectPoints))

#building ba problem
baProblem = ba.BaProblem(listOfObjectPointCollections = listOfObjectPoints, listOfImageCollections = listOfImageCollections, baSettings = ba.BaSettings())
sfmio.writeRaysToDxf("rays_tie.dxf",baProblem.objectPointsCollections, baProblem.imageCollections ,"tie",9)
sfmio.writeRaysToDxf("rays_controll.dxf",baProblem.objectPointsCollections, baProblem.imageCollections ,"controll",1)

xtrelio.writeBaProblem(outputXtrelDirectoryName, baProblem)