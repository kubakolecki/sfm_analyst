import sfmio
import xtrelio
import geometry
import rasterio
import sgen
import ba_problem as ba
import numpy as np

#all paths are relative

flightMissionImages = geometry.ImageCollection(collectionId = 0) #creating empty collection of images with id = 0
# We create our camera:
missionCamera = geometry.PinholeCamera(name = "myCamera" , pixelSizeMilimeters=0.004, numberOfRows = 4000, numberOfColumns= 6000, principalDistanceMilimeters = 20.0)
baSettings = xtrelio.readBaSettings("ExampleSimulateBaProblem/inputData/baconfig.yaml") #Reading settings for our problem
outputXtrelDirectoryName = "ExampleSimulateBaProblem/CaliforniaBaProblem"
sfmio.importFromExternalOrientationTextfile("ExampleSimulateBaProblem/inputData/CaliforniaEO.txt",' ', #importing external orientation for our images
                                           flightMissionImages,
                                           "xyz",
                                           observedPosition = False,
                                           observedOrientation = False,
                                           camera = missionCamera )
sfmio.writeImageCollectionToObj(flightMissionImages, "ExampleSimulateBaProblem/outputAndVisualisation/california", imageWidthInMeters = 12, axesLenghtInMeters = 7.0)

#generating structure
dsm = rasterio.open("ExampleSimulateBaProblem/inputData/CaliforniaDSM.tif", driver="GTiff")

listOfImageCollections = []
listOfImageCollections.append(flightMissionImages)

stdDevControllPoints = np.array([baSettings.noiseForControllPoints[1][0], baSettings.noiseForControllPoints[1][1], baSettings.noiseForControllPoints[1][2] ])

structGenConfigTie = sgen.StructGenConfig(cellSize = 65, pointsPerCell = 2, dispersion = 1.5, approach = "uniform")
structGenConfigControll = sgen.StructGenConfig(cellSize = 65, pointsPerCell = 1, dispersion= 1.0, standardDeviation = stdDevControllPoints, approach = "uniform", typeOfPoints= "controll")
structGenConfigCheck = sgen.StructGenConfig(cellSize = 100, pointsPerCell = 1, dispersion= 1.0, approach = "uniform", typeOfPoints= "check")

#Generate the bounding box on the terrain to deal with:
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


#If you wish your dsm to be saved as obj uncomment this line, but note that wirting to obj may take some time
#sfmio.writeSurfaceModelToObj("ExampleSimulateBaProblem/outputAndVisualisation/dsm.obj", dsm, imageRange)

#building and saving ba problem
baProblem = ba.BaProblem(listOfObjectPointCollections = listOfObjectPoints, listOfImageCollections = listOfImageCollections, baSettings = baSettings)
xtrelio.writeBaProblem(outputXtrelDirectoryName, baProblem)

#If you wish you can save points and rays for visualization
sfmio.writeRaysToDxf("ExampleSimulateBaProblem/outputAndVisualisation/rays_tie.dxf",baProblem.objectPointsCollections, baProblem.imageCollections ,"tie",9)
sfmio.writeRaysToDxf("ExampleSimulateBaProblem/outputAndVisualisation/rays_controll.dxf",baProblem.objectPointsCollections, baProblem.imageCollections ,"controll",1)
sfmio.writeObjectPointsToFile("ExampleSimulateBaProblem/outputAndVisualisation/objectPointsTie.txt", objectPointsTie)
sfmio.writeObjectPointsToFile("ExampleSimulateBaProblem/outputAndVisualisation/objectPointsControll.txt", objectPointsControll)
