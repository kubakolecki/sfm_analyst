import sfmio
import xtrelio
import geometry
import ba_problem as ba
import numpy as np
import os as os
import subprocess
import time

if __name__ == '__main__':

    projectName = "ComplexDroneFilght"
    pathFileXtrel = r"D:\DANE\xtrel\xtrel.exe"

    pathDirectoryInputData = r"D:\DANE\Visual_Studio\Python\sfm_analyst\sfm_analyst\ExampleSimulateBaProblem\inputData"
    pathDirecotryOutputBAProblem = r"D:\DANE\Visual_Studio\Python\sfm_analyst\sfm_analyst\ExampleSimulateBaProblem\ComplexGeometryProblem"
    pathDirectoryOutputRsults = r"D:\DANE\Visual_Studio\Python\sfm_analyst\sfm_analyst\ExampleSimulateBaProblem\outputAndVisualisationComplexGeometryProblem"

    pathFileInputConfg = os.path.join(pathDirectoryInputData,"baconfig_complex_geometry.yaml")
    pathFileInputEoSide = os.path.join(pathDirectoryInputData,"bridge_eo_side.txt")
    pathFileInputEoTop = os.path.join(pathDirectoryInputData,"bridge_eo_top.txt")

    pathFileTiePoints = os.path.join(pathDirectoryInputData,"bridge_tie_points.txt")
    pathFileControlPoints = os.path.join(pathDirectoryInputData,"bridge_control_points.txt") 

    pathFileOutputRaysTie = os.path.join(pathDirectoryOutputRsults,"rays_tie.dxf")
    pathFileOutputRaysControl = os.path.join(pathDirectoryOutputRsults,"rays_control.dxf")
    pathFileOutputTiePoints = os.path.join(pathDirectoryOutputRsults,"objectPointsTie.txt")
    pathFileOutputControlPoints = os.path.join(pathDirectoryOutputRsults,"objectPointsControl.txt")

    imageCollection = geometry.ImageCollection(collectionId = 0)
    
    camera = geometry.PinholeCamera(name = "myCamera" , pixelSizeMilimeters=0.004, numberOfRows = 4000, numberOfColumns= 6000, principalDistanceMilimeters = 20.0)
    baSettings = xtrelio.readBaSettings("ExampleSimulateBaProblem/inputData/baconfig_complex_geometry.yaml") #Reading settings for our problem

    sfmio.importFromExternalOrientationTextfile(pathFileInputEoSide,' ', #importing external orientation for our side images
                                               imageCollection,
                                               "ZXZ",
                                               observedPosition = False,
                                               observedOrientation = False,
                                               camera = camera )

    sfmio.importFromExternalOrientationTextfile(pathFileInputEoTop,' ', #importing external orientation for our top images - note the difference in the order of rotation
                                               imageCollection,
                                               "XYZ",
                                               observedPosition = False,
                                               observedOrientation = False,
                                               camera = camera )

    tiePointCollection = geometry.ObjectPointCollection(collectionId = 0)
    controlPointCollection = geometry.ObjectPointCollection(collectionId = 1) 

    tiePointsData = np.loadtxt(pathFileTiePoints, dtype=float, delimiter=',', skiprows=1)
    tiePointCollection.reserve(tiePointsData.shape[0])
    for i in range(0,tiePointsData.shape[0]):
        tiePointCollection.insertPointWithNormalAndVisibilityDistance(tiePointsData[i,1], tiePointsData[i,2], tiePointsData[i,3], 0.001, 0.001, 0.001, tiePointsData[i,4], tiePointsData[i,5], tiePointsData[i,6], tiePointsData[i,7], "tie", int(tiePointsData[i,0]), i)

    controlPointsData = np.loadtxt(pathFileControlPoints, dtype=float, delimiter=',', skiprows=1)
    controlPointCollection.reserve(controlPointsData.shape[0])
    for i in range(0,controlPointsData.shape[0]):
        controlPointCollection.insertPointWithNormalAndVisibilityDistance(controlPointsData[i,1], controlPointsData[i,2], controlPointsData[i,3], controlPointsData[i,4], controlPointsData[i,5], controlPointsData[i,6], controlPointsData[i,7], controlPointsData[i,8], controlPointsData[i,9], controlPointsData[i,10], "control", int(controlPointsData[i,0]), i)
    

    listOfObjectPoints = [tiePointCollection, controlPointCollection]
    

    baProblem = ba.BaProblem(listOfObjectPointCollections = listOfObjectPoints, listOfImageCollections = [imageCollection], baSettings = baSettings)
    baProblem.baSettings.computeRedundancy = 1
    baProblem.baSettings.computeCorrelations = 0
    xtrelio.writeBaProblem(pathDirecotryOutputBAProblem, baProblem)

    sfmio.write3DVisualizationOfImages(imageCollection = imageCollection,outputDirectory = pathDirectoryOutputRsults,  nameOf3DModel = projectName, imageWidthInMeters = 0.3, axesLenghtInMeters = 0.2)
    sfmio.writeRaysToDxf(pathFileOutputRaysTie, baProblem.objectPointsCollections, baProblem.imageCollections ,"tie",9)
    sfmio.writeRaysToDxf(pathFileOutputRaysControl,baProblem.objectPointsCollections, baProblem.imageCollections ,"control",1)
    sfmio.writeObjectPointsToFile(pathFileOutputTiePoints, tiePointCollection)
    sfmio.writeObjectPointsToFile(pathFileOutputControlPoints, controlPointCollection)



    pathFileConfigBA = os.path.join(pathDirecotryOutputBAProblem,"config.yaml")

    print("starting xtrel")
    timeStart = time.monotonic_ns()
    completedProcess = subprocess.run([pathFileXtrel,pathFileConfigBA], capture_output=True )
    timeEnd = time.monotonic_ns()
    print(f"xtrel process finished wiht code: {completedProcess.returncode}, elapsed time: {timeEnd - timeStart}")