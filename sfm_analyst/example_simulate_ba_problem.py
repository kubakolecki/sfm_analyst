import sfmio
import xtrelio
import geometry
import rasterio
import raster_based_analysis as rba
import sgen
import ba_problem as ba
import numpy as np
import os as os
import subprocess
import time

if __name__ == '__main__':
    
    projectName = "California"
    
    pathDirectoryInputData = r"D:\DANE\Visual_Studio\Python\sfm_analyst\sfm_analyst\ExampleSimulateBaProblem\inputData"
    pathDirecotryOutputBAProblem = r"D:\DANE\Visual_Studio\Python\sfm_analyst\sfm_analyst\ExampleSimulateBaProblem\CaliforniaBaProblem"
    pathDirectoryOutputRsults = r"D:\DANE\Visual_Studio\Python\sfm_analyst\sfm_analyst\ExampleSimulateBaProblem\outputAndVisualisation"
    
    pathFileXtrel = r"D:\DANE\xtrel\xtrel.exe"
    
    pathFileInputConfg = os.path.join(pathDirectoryInputData,"baconfig_eo_noise.yaml")
    pathFileInputEO = os.path.join(pathDirectoryInputData,"California30EO.txt")
    pathFileInputDSM = os.path.join(pathDirectoryInputData,"CaliforniaDSM.tif")
    
    pathFileOutputImageOverlap = os.path.join(pathDirectoryOutputRsults,"overlap.tif")
    pathFileOutputRaysTie = os.path.join(pathDirectoryOutputRsults,"rays_tie.dxf")
    pathFileOutputRaysControl = os.path.join(pathDirectoryOutputRsults,"rays_control.dxf")
    pathFileOutputTiePoints = os.path.join(pathDirectoryOutputRsults,"objectPointsTie.txt")
    pathFileOutputControlPoints = os.path.join(pathDirectoryOutputRsults,"objectPointsControl.txt")
    
    flightMissionImages = geometry.ImageCollection(collectionId = 0) #creating empty collection of images with id = 0
    # We create our camera:
    missionCamera = geometry.PinholeCamera(name = "myCamera" , pixelSizeMilimeters=0.004, numberOfRows = 4000, numberOfColumns= 6000, principalDistanceMilimeters = 20.0)
    baSettings = xtrelio.readBaSettings(pathFileInputConfg) #Reading settings for our problem
    
    sfmio.importFromExternalOrientationTextfile(pathFileInputEO,' ', #importing external orientation for our images
                                               flightMissionImages,
                                               "xyz",
                                               observedPosition = False,
                                               observedOrientation = False,
                                               camera = missionCamera )
    sfmio.write3DVisualizationOfImages(imageCollection = flightMissionImages, outputDirectory = pathDirectoryOutputRsults, nameOf3DModel = projectName, imageWidthInMeters = 12, axesLenghtInMeters = 7.0)
    
    #generating structure
    dsm = rasterio.open(pathFileInputDSM, driver="GTiff")
    
    listOfImageCollections = []
    listOfImageCollections.append(flightMissionImages)
    
    stdDevControllPoints = np.array([baSettings.noiseForControllPoints[1][0], baSettings.noiseForControllPoints[1][1], baSettings.noiseForControllPoints[1][2] ])
    
    structGenConfigTie = sgen.StructGenConfig(cellSize = 65, pointsPerCell = 4, dispersion = 1.5, approach = "uniform")
    structGenConfigControll = sgen.StructGenConfig(cellSize = 65, pointsPerCell = 1, dispersion= 1.0, standardDeviation = stdDevControllPoints, approach = "uniform", typeOfPoints= "control")
    structGenConfigCheck = sgen.StructGenConfig(cellSize = 100, pointsPerCell = 1, dispersion= 1.0, approach = "uniform", typeOfPoints= "check")
    
    #Generate the bounding box on the terrain to deal with:
    imageRange = sgen.generateProcessingRangeFromImages(rasterioDsm = dsm, listOfImageCollections = listOfImageCollections)
    
    imageOverlapMulti, projectionsOfDSM = rba.computeImageOverlapMultiprocess(rasterioDsm = dsm, listOfImageCollections = listOfImageCollections, numberOfProcesses = 8)
    
    
    print("number of dsm points to estimate in intersection: ", len(projectionsOfDSM) )

    
    triangulatedObjectPoints = rba.triangulatePointsMultiprocess(projectionsOfDSM, listOfImageCollections, 8)


    overlapTargetProfile = dsm.profile.copy()
    
    overlapTargetProfile.update(
        dtype = rasterio.int32,
        nodata = -1.0,
        count = 1)
    
    #print("writing overlap in ", os.path.join(outputXtrelDirectoryName,"overlap.tif"))
    print("writing overlap in ", pathFileOutputImageOverlap)
    
    #with rasterio.open(os.path.join(outputXtrelDirectoryName,"overlap.tif"), 'w', **kwargs) as overlapRaster:
    #overlapRaster = rasterio.open(os.path.join(outputXtrelDirectoryName,"overlap.tif"), mode='w', **kwargs) 
    overlapRaster = rasterio.open(pathFileOutputImageOverlap, mode='w', **overlapTargetProfile)
    overlapRaster.write(imageOverlapMulti.astype(rasterio.float32),1)
    overlapRaster.close()
    
    print("imageRange:")
    print("bottom-left:", imageRange.bottomLeft)
    print("top-right:", imageRange.topRight)
    
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
    xtrelio.writeBaProblem(pathDirecotryOutputBAProblem, baProblem)
    
    #If you wish you can save points and rays for visualization
    sfmio.writeRaysToDxf(pathFileOutputRaysTie, baProblem.objectPointsCollections, baProblem.imageCollections ,"tie",9)
    sfmio.writeRaysToDxf(pathFileOutputRaysControl,baProblem.objectPointsCollections, baProblem.imageCollections ,"control",1)
    sfmio.writeObjectPointsToFile(pathFileOutputTiePoints, objectPointsTie)
    sfmio.writeObjectPointsToFile(pathFileOutputControlPoints, objectPointsControll)

    pathFileConfigBA = os.path.join(pathDirecotryOutputBAProblem,"config.yaml")

    print("starting xtrel")
    timeStart = time.monotonic_ns()
    completedProcess = subprocess.run([pathFileXtrel,pathFileConfigBA], capture_output=True )
    timeEnd = time.monotonic_ns()
    print(f"xtrel process finished wiht code {completedProcess.returncode}, elapsed time {timeEnd - timeStart}")

    imageCollectionOptimized = xtrelio.createImageCollectionFromXtrelReport(os.path.join(pathDirecotryOutputBAProblem,"report.txt"), 0)

    print("optimized image collection:")
    print(f"collection id = {imageCollectionOptimized.id}")
    for key, image in imageCollectionOptimized.images.items():
        print(f"image id = {key}, position: {image.pose.translation[0,0]}, {image.pose.translation[1,0]} ,{image.pose.translation[2,0]}")


    coordinatesToEvaluate = rba.triangulatePointsMultiprocess(projectionsOfDSM, [imageCollectionOptimized], 8)
    rba.computeResidualRasters(dsm,coordinatesToEvaluate)
    