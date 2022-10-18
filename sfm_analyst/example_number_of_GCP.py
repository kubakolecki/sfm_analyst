import sfmio
import xtrelio
import geometry
import sgen
import ba_problem as ba

import rasterio
import numpy as np
import os
import time

#the accuracy of control points is to be set in config *.yaml file

flightMissionImages = geometry.ImageCollection(collectionId = 0) #creating empty collection of images with id = 0
# We create our camera:
# missionCamera = geometry.PinholeCamera(name = "myCamera" , pixelSizeMilimeters=0.004, numberOfRows = 4000, numberOfColumns= 6000, principalDistanceMilimeters = 20.0)
missionCamera = geometry.PinholeCamera(name = "DJIPhantom4PRO" , pixelSizeMilimeters=0.0024, numberOfRows = 3648, numberOfColumns= 5472, principalDistanceMilimeters = 8.8 )
#missionCamera.setCalibrationFlags([0, 0, 0, 0]) #uncomment this to optimize with camera calibration

baSettings = xtrelio.readBaSettings("ExampleSimulateBaProblem/inputData/baconfig_eo_large_noise.yaml") #Reading settings for our problem
outputXtrelDirectoryName = "ExampleSimulateBaProblem/baProblem"
# eozFile = "ExampleSimulateBaProblem/inputData/CaliforniaEO.txt"
eozFile = "ExampleSimulateBaProblem/inputData/EOZ_zielonki.txt"
sfmio.importFromExternalOrientationTextfile(eozFile,' ', #importing external orientation for our images
                                           flightMissionImages,
                                           "xyz",
                                           observedPosition = False,
                                           observedOrientation = False,
                                           camera = missionCamera )
sfmio.writeImageCollectionToObj(flightMissionImages, "ExampleSimulateBaProblem/outputAndVisualisation/zielonki", imageWidthInMeters = 12, axesLenghtInMeters = 7.0)

#generating structure
#dsm = rasterio.open("ExampleSimulateBaProblem/inputData/CaliforniaDSM.tif", driver="GTiff")
dsm = rasterio.open("ExampleSimulateBaProblem/inputData/DEM_zielonki.tif", driver="GTiff")

listOfImageCollections = []
listOfImageCollections.append(flightMissionImages)

stdDevControllPoints = np.array([baSettings.noiseForControllPoints[1][0], baSettings.noiseForControllPoints[1][1], baSettings.noiseForControllPoints[1][2] ])

#Generate the bounding box on the terrain to deal with:
imageRange = sgen.generateProcessingRangeFromImages(rasterioDsm = dsm, listOfImageCollections = listOfImageCollections)

#we have to set this to avoid reports beeing overwritten:
baSettings.placeRaportInProjectDirecotry = False 
baSettings.reportDirectory = "D:/DANE/Visual_Studio/Python/sfm_analyst/sfm_analyst/ExampleSimulateBaProblem/baReports"

#Following lines are to set the density of tie and check points. Decrease cell size and/or increase points per cell to increase the number of tie/check points
structGenConfigTie = sgen.StructGenConfig(cellSize = 30, pointsPerCell = 10, dispersion = 1.5, approach = "uniform")
structGenConfigCheck = sgen.StructGenConfig(cellSize = 50, pointsPerCell = 1, dispersion= 1.0, approach = "uniform", typeOfPoints= "check")
objectPointsTie = sgen.generateUsingSurfaceModel(rasterioDsm = dsm, givenRange = imageRange, generationConfig = structGenConfigTie, id = 0)
objectPointsCheck = sgen.generateUsingSurfaceModel(rasterioDsm = dsm, givenRange = imageRange, generationConfig = structGenConfigCheck, id = 2)

GCPCellSizeRange = range(140,14,-2) #iterating through this range will impact the number of control points
NumOfSamples = 5 #how many samle to use for each gcp cell size

for cellSz in GCPCellSizeRange:
    structGenConfigControll = sgen.StructGenConfig(cellSize = cellSz, pointsPerCell = 1, dispersion= 1.0, standardDeviation = stdDevControllPoints, approach = "uniform", typeOfPoints= "control")
    objectPointsControll = sgen.generateUsingSurfaceModel(rasterioDsm = dsm, givenRange = imageRange, generationConfig = structGenConfigControll, id = 1)
    listOfObjectPoints = [objectPointsTie, objectPointsControll, objectPointsCheck]
  
    baProblem = ba.BaProblem(listOfObjectPointCollections = listOfObjectPoints, listOfImageCollections = listOfImageCollections, baSettings = baSettings)
    for sample in range(0,NumOfSamples):
        baSettings.reportFileName = "report_" + str(cellSz) + "_" + str(sample) + ".txt"
        xtrelio.writeBaProblem(outputXtrelDirectoryName, baProblem)
        os.startfile("D:/DANE/Visual_Studio/Python/sfm_analyst/sfm_analyst/ExampleSimulateBaProblem/runxtrel.bat")
        time.sleep(4) #this is important to set - we have to wait until solver finishes, if you have slow computer set this to some higher value

