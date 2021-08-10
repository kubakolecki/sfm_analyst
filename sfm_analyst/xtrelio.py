import geometry
import conversions as conv
import numpy as np
import ba_problem as ba
import csv as csv
import os as os
import shutil as sh
import scipy.spatial.transform as transf

def createImageCollectionFromXtrelReport(filename, collectionId):
    reportFile = open(filename,"r")
    lines = reportFile.readlines()
    numberOfImages = 0
    #looking for line with number of images:
    for line in lines:
        if len(line) < 28:
            continue
        if line[0:27] == "Number of images          :":
            elements = line.split()
            numberOfImages = int(elements[len(elements)-1])
    
    positionOfCameras = lines.index("Cameras assignments and number of points:\n")
    cameraAssignments = {}
    cameraFiles = set()

    #reading file names of cameras
    for lineId in range(positionOfCameras+2, positionOfCameras + 2 + numberOfImages):
        elements = lines[lineId].split()
        cameraAssignments[elements[0]] = elements[1]
        cameraFiles.add(elements[1])
    
    cameras = {}
    for cameraFile in cameraFiles:
        try:
            camera = readCameraFromCamFile(cameraFile)
            cameras[cameraFile] = camera
        except:
            print("Error while reading camera from cam file")
    
    #reading coordinates of projection centers
    positionOfCoordinatesStart = lines.index("Coordinates:\n")
    projectionCenterCoordinates = {}
    for lineId in range(positionOfCoordinatesStart+2, positionOfCoordinatesStart + 2 + numberOfImages):
        elements = lines[lineId].split()
        imageId = elements[1]
        coordinates = np.zeros((3,1))
        coordinates[0,0] = float(elements[2])
        coordinates[1,0] = float(elements[3])
        coordinates[2,0] = float(elements[4])
        projectionCenterCoordinates[imageId] = coordinates

    #reading rotation
    positionOfRotationsStart = lines.index("Rotation:\n")
    anglesRad = {}
    parametrization = {}
    for lineId in range(positionOfRotationsStart+2, positionOfRotationsStart + 2 + numberOfImages):
        elements = lines[lineId].split()
        imageId = elements[1]
        angles = np.zeros(3)
        angles[0] = conv.degrees2Radians(float(elements[3]))
        angles[1] = conv.degrees2Radians(float(elements[4]))
        angles[2] = conv.degrees2Radians(float(elements[5]))
        anglesRad[imageId] = angles
        parametrization[imageId] = elements[2]

    reportFile.close()

    #building collection:
    mapRotationSequenceToName = {"om-fi-ka" : "xyz", "al-ni-ka" : "zxz" }

    collectionOfImages = geometry.ImageCollection(collectionId = collectionId)

    for imageId, position in projectionCenterCoordinates.items():
        pose = geometry.Pose()
        pose.setTranslation(position)
        pose.setRotationEuler(anglesRad[imageId], mapRotationSequenceToName[parametrization[imageId]] )
        image = geometry.Image()
        image.setPose(pose)
        image.setCamera(cameras[cameraAssignments[imageId]])
        image.rotationSequence = mapRotationSequenceToName[parametrization[imageId]]
        collectionOfImages.addImage(image, imageId)

    return collectionOfImages

def createObjectPointCollectionFromXtrelReport(filename, objectCollectionId, imageCollectionId):
    reportFile = open(filename,"r")
    lines = reportFile.readlines()
    numberOfControllPoints = 0
    numberOfTiePoints = 0
    numberOfCheckPoints = 0
    for line in lines:
        if len(line) < 28:
            continue
        if line[0:27] == "Number of controll points :":
            elements = line.split()
            numberOfControllPoints = int(elements[len(elements)-1])
        if line[0:27] == "Number of tie points      :":
            elements = line.split()
            numberOfTiePoints = int(elements[len(elements)-1])
        if line[0:27] == "Number of check points    :":
            elements = line.split()
            numberOfCheckPoints = int(elements[len(elements)-1])
            break
    
    numberOfObjectPoints = numberOfControllPoints + numberOfTiePoints + numberOfCheckPoints
    positionOfObjectPoints = lines.index("Estimated coordinates of object points:\n")

    pointIds = set()
    pointTypes = {}
    pointCoordinates = {}
    for lineId in range(positionOfObjectPoints + 3, positionOfObjectPoints + 3 + numberOfObjectPoints):
        elements = lines[lineId].split()
        pointIds.add(elements[0])
        pointTypes[elements[0]] = int(elements[1])
        coordinatesAndStandardDeviations = []
        for columnId in range(3,9):
            coordinatesAndStandardDeviations.append(float(elements[columnId]))
        pointCoordinates[elements[0]] = coordinatesAndStandardDeviations

    correspondences = {}

    for pointId in pointIds:
        correspondences[pointId] = []

    positionOfImagePointResiduals = lines.index("Image points residuals: \n")

    for lineId in range(positionOfImagePointResiduals + 2, len(lines)):
        elements = lines[lineId].split()
        if len(elements) != 5:
            break
        correspondences[elements[0]].append((imageCollectionId, elements[1]))
    
    objectPointCollection = geometry.ObjectPointCollection(collectionId = objectCollectionId)
    objectPointCollection.reserve(len(pointCoordinates))

    idToTypeMap = {0 : "tie", 3 : "controll", 4 : "check"}
    positionInArray = 0
    for pointId, coordinates in pointCoordinates.items():
        objectPointCollection.insertPoint(
            coordinates[0], coordinates[1], coordinates[2],
            coordinates[3], coordinates[4], coordinates[5],
            idToTypeMap[pointTypes[pointId]], pointId, positionInArray)
        objectPointCollection.imagesIds[positionInArray] = correspondences[pointId]
        positionInArray = positionInArray + 1
    
    return objectPointCollection
  
def getCheckPointRMSEFromXtrelReport(filename):
    reportFile = open(filename,"r")
    lines = reportFile.readlines()
    numberOfCheckPoints = 0

    for line in lines:
        if len(line) < 28:
            continue
        if line[0:27] == "Number of check points    :":
            elements = line.split()
            numberOfCheckPoints = int(elements[len(elements)-1])
            break
    
    positionOfCheckPointsResiduals = lines.index("Differences in check point coordinates (given - estimated), sorted:\n")

    elements = lines[positionOfCheckPointsResiduals + numberOfCheckPoints + 3].split()

    residuals = np.zeros((4,1))
    residuals[0,0] = elements[1]
    residuals[1,0] = elements[3]
    residuals[2,0] = elements[5]
    residuals[3,0] = elements[7]

    reportFile.close()

    return residuals

def readCameraFromCamFile(filename):
    if checkCameraFile(filename) == False:
        raise
    cameraFile = open(filename)
    lines = cameraFile.readlines()
    name = lines[1].split()[0]
    numberOfColumns = int(lines[3].split()[0])
    numberOfRows = int(lines[3].split()[1])
    principalDistancePixels = float(lines[5].split()[0])
    x0 = float(lines[6].split()[0])
    y0 = float(lines[7].split()[0])
    pixelSizeInMilmeters = float(lines[21].split()[0])
    principalDistanceMilimeters = principalDistancePixels*pixelSizeInMilmeters
    camera = geometry.PinholeCamera(name = name, pixelSizeMilimeters =  pixelSizeInMilmeters,
                                   numberOfRows = numberOfRows, numberOfColumns = numberOfColumns,
                                   principalDistanceMilimeters = principalDistanceMilimeters)
    return camera
    
def checkCameraFile(filename):
    cameraFile = open(filename)
    lines = cameraFile.readlines()
    result = True
    if len(lines) != 30:
        print("ERROR in readCameraFromCamFile! ",filename, " does not contain valid camera." )
        print("Camera file should contain 30 lines.")
        result = False
    
    if lines[0].split()[0] != "Name:":
        print("ERROR in readCameraFromCamFile! ",filename, " does not contain valid camera." )
        print("\"Name:\" tag is missing or is missplaced")
        result = False
    
    if lines[2].split()[0] != "Size:":
        print("ERROR in readCameraFromCamFile! ",filename, " does not contain valid camera." )
        print("\"Size:\" tag is missing or is missplaced")
        result = False

    if lines[4].split()[0] != "Interior:":
        print("ERROR in readCameraFromCamFile! ",filename, " does not contain valid camera." )
        print("\"Interior:\" tag is missing or is missplaced")
        result = False

    if lines[8] != "Radial distortion:\n":
        print("ERROR in readCameraFromCamFile! ",filename, " does not contain valid camera." )
        print("\"Radial distortion:\" tag is missing or is missplaced")
        result = False

    if lines[12] != "Tangential distortion:\n":
        print("ERROR in readCameraFromCamFile! ",filename, " does not contain valid camera." )
        print("\"Tangential distortion:\" tag is missing or is missplaced")
        result = False

    if lines[19].split()[0] != "Additional_data:":
        print("ERROR in readCameraFromCamFile! ",filename, " does not contain valid camera." )
        print("\"Additional_data:\" tag is missing or is missplaced")
        result = False

    if lines[20].split()[0] != "Pixel_size[mm]:":
        print("ERROR in readCameraFromCamFile! ",filename, " does not contain valid camera." )
        print("\"Pixel_size[mm]:\" tag is missing or is missplaced")
        result = False

    if lines[26].split()[0] != "Lens_nominal_focal_length[mm]:":
        print("ERROR in readCameraFromCamFile! ",filename, " does not contain valid camera." )
        print("\"Lens_nominal_focal_length[mm]:\" tag is missing or is missplaced")
        result = False

    if len(lines[3].split()) != 2:
        print("ERROR in readCameraFromCamFile! ",filename, " does not contain valid camera." )
        print("Number of rows and colums is not provided or is ill formated")
        result = False

    if len(lines[5].split()) != 2:
        print("ERROR in readCameraFromCamFile! ",filename, " does not contain valid camera." )
        print("The way the principal distance is stored in the camera file is wrong")
        result = False

    if len(lines[6].split()) != 2:
        print("ERROR in readCameraFromCamFile! ",filename, " does not contain valid camera." )
        print("The way the x coordinate of principal point is stored in the camera file is wrong")
        result = False

    if len(lines[7].split()) != 2:
        print("ERROR in readCameraFromCamFile! ",filename, " does not contain valid camera." )
        print("The way the y coordinate of principal point is stored in the camera file is wrong")
        result = False


    result = True
    cameraFile.close()
    return result

def writeObjectPointCollectionsToFile(filename, objectPointCollections, noise = {} ):
    typeToIdMap = {"tie" : 0, "controll" : 3, "check" : 4}
    file = open(filename,"w")
    for objectPointCollection in objectPointCollections:
        randomNumberGenerator =  np.random.default_rng()
        addNoise = False
        if objectPointCollection.collectionId in noise:
            addNoise = True
        npoints = objectPointCollection.getNumberOfPoints()
        for i in range(0,npoints):
            file.write("%s " % objectPointCollection.getCombinedPointName(i) )
            dx = 0
            dy = 0
            dz = 0
            if addNoise:
                dx = randomNumberGenerator.normal(0.0, noise[objectPointCollection.collectionId][0], 1)
                dy = randomNumberGenerator.normal(0.0, noise[objectPointCollection.collectionId][1], 1)
                dz = randomNumberGenerator.normal(0.0, noise[objectPointCollection.collectionId][2], 1)
            file.write("%.5f %.5f %.5f " % (objectPointCollection.coordinates[0,i] + dx, objectPointCollection.coordinates[1,i] + dy, objectPointCollection.coordinates[2,i] + dz))
            file.write("%d " % typeToIdMap[objectPointCollection.types[i]])
            file.write("%.5f %.5f %.5f\n" % (objectPointCollection.standardDeviations[0,i], objectPointCollection.standardDeviations[1,i], objectPointCollection.standardDeviations[2,i]))
    file.close()

def writeBaProblem(projectName, baProblem):
    
    mapRotationSequenceToName = {"xyz" : "om-fi-ka", "zxz" : "al-ni-ka" }
    workingDirectory = os.getcwd()
    projectDirectory = os.path.join(workingDirectory, projectName)
    if os.path.isdir(projectDirectory):
        sh.rmtree(projectDirectory)
    
    try:
        os.mkdir(projectDirectory)
    except OSError:
        print ("ERROR: Creation of the BA project directory %s failed" % projectDirectory)
    else:
        print ("Successfully created the BA project directory %s " % projectDirectory)

    #writing camera:
    for cameraName, camera in baProblem.mapOfCameras.items():
        cameraFileName = cameraName + ".cam"
        cameraFile = open(os.path.join(projectDirectory,cameraFileName),"w")
        cameraFile.write("Name:\n")
        cameraFile.write("%s\n" % camera.name)
        cameraFile.write("Size:\n")
        cameraFile.write("%d %d\n" % (camera.width, camera.height) )
        cameraFile.write("Interior:\n")
        cameraFile.write("%.4f 2.0\n" % -camera.cameraMatrix[0,0])
        cameraFile.write("%.4f 2.0\n" % camera.cameraMatrix[0,2])
        cameraFile.write("%.4f 2.0\n" % camera.cameraMatrix[1,2])
        cameraFile.write("Radial distortion:\n")
        cameraFile.write("0 3\n")
        cameraFile.write("0 3\n")
        cameraFile.write("0 3\n")
        cameraFile.write("Tangential distortion:\n")
        cameraFile.write("0 3\n")
        cameraFile.write("0 3\n")
        cameraFile.write("Y scaling:\n")
        cameraFile.write("0 3\n")
        cameraFile.write("Skewness of axes:\n")
        cameraFile.write("0 3\n")
        cameraFile.write("Additional_data:\n")
        cameraFile.write("Pixel_size[mm]:\n")
        cameraFile.write("%.7f\n" % camera.pixelSizeMilimeters)
        cameraFile.write("Camera_serial_number:\n")
        cameraFile.write("SN1234567890\n")
        cameraFile.write("Lens_name:\n")
        cameraFile.write("Unknown:\n")
        cameraFile.write("Lens_nominal_focal_length[mm]:\n")
        cameraFile.write("%d\n" % int(np.round(-camera.cameraMatrix[0,0] *camera.pixelSizeMilimeters)))
        cameraFile.write("Lens_serial_number:\n")
        cameraFile.write("SN9876543210\n")
        cameraFile.close()

    #writing external orientation:

    eoFile = open(os.path.join(projectDirectory,"eo.txt"),"w")
    eoFile.write("eofile_v20210309\n")
    for i in range(0, len(baProblem.imageCollections)):
        for imageId, image in baProblem.imageCollections[i].images.items():
            id = str(i) + "_" + imageId
            eoFile.write("%s " % id)
            rot = transf.Rotation.from_matrix(image.pose.rotation)
            angles = rot.as_euler(image.rotationSequence,degrees = True)
            eoFile.write("%.5f %.5f %.5f " % (image.pose.translation[0,0], image.pose.translation[1,0], image.pose.translation[2,0] ))
            eoFile.write("%.5f %.5f %.5f " % (angles[0], angles[1], angles[2]))
            eoFile.write("%.5f %.5f %.5f " % (image.pose.stdDevTranslation[0], image.pose.stdDevTranslation[1], image.pose.stdDevTranslation[2] ))
            eoFile.write("%.5f %.5f %.5f " % (image.pose.stdDevRotation[0], image.pose.stdDevRotation[1], image.pose.stdDevRotation[2] ))
            eoFile.write("%d %d " % (baProblem.imageCollections[i].observedPosition, baProblem.imageCollections[i].observedOrientation  ))
            eoFile.write("%s "% mapRotationSequenceToName[image.rotationSequence] )
            cameraFileName = os.path.join(projectDirectory,image.camera.name + ".cam")
            eoFile.write("%s 1\n" % cameraFileName)
    eoFile.close()

    #writing image point measurements

    imagePointFile = open(os.path.join(projectDirectory,"image_observations.txt"),"w")
    randomNumberGenerator =  np.random.default_rng()
    for imageId, listOfMeasurements in baProblem.imagePointsPerImage.items():
        imagePointFile.write("%s\n" % imageId)
        for imagePoint in listOfMeasurements:
            dx = 0.0
            dy = 0.0
            if baProblem.baSettings.noiseForImagePoints > 0:
                dx = randomNumberGenerator.normal(0.0, baProblem.baSettings.noiseForImagePoints, 1)
                dy = randomNumberGenerator.normal(0.0, baProblem.baSettings.noiseForImagePoints, 1)
            imagePointFile.write("%s %.4f %.4f 1\n" % (imagePoint.getCombinedPointName(), imagePoint.observation.x + dx, imagePoint.observation.y + dy ))
    imagePointFile.close()

    #writing object points to file
    objectPointFile = os.path.join(projectDirectory,"object_points.txt")

    writeObjectPointCollectionsToFile(objectPointFile, baProblem.objectPointsCollections, baProblem.baSettings.noiseForControllPoints)
    print("using noise: ")
    print(baProblem.baSettings.noiseForControllPoints)

    #writing config file
    configFile = open(os.path.join(projectDirectory,"config.yaml"),"w")
    configFile.write("NumOfCameras: %d\n" % len(baProblem.mapOfCameras))
    configFile.write("MathModel: SOFT\n")
    configFile.write("ImageMesAcc: %.6f\n" % baProblem.baSettings.noiseForImagePoints)
    configFile.write("HzAngleMesAcc: 10\n")
    configFile.write("VAngleMesAcc: 10\n")
    configFile.write("DistMesAcc: 0.00200\n")
    configFile.write("LossFunction: NONE\n")
    configFile.write("LossFunctionParameter: 1.5\n")
    configFile.write("CamFixMasks:\n")
    for cameraName, camera in baProblem.mapOfCameras.items():
        cameraFileName = cameraName + ".cam"
        cameraFile = os.path.join(projectDirectory,cameraFileName)
        configFile.write("%s: %d%d%d%d\n" % (cameraFile, camera.calibrationFlags[0], camera.calibrationFlags[1], camera.calibrationFlags[2], camera.calibrationFlags[3] ))
    configFile.write("ComputeCorrelations: %d\n" % baProblem.baSettings.computeCorrelations)
    configFile.write("ComputeRedundancy: %d\n" % baProblem.baSettings.computeRedundancy)
    configFile.write("GenerateCalibrationCertificate: 0\n")
    configFile.write("FilenameImagePoints: '%s'\n" % os.path.join(projectDirectory, "image_observations.txt"))
    configFile.write("FilenameObjectPoints: '%s'\n" % os.path.join(projectDirectory, "object_points.txt"))
    configFile.write("FilenameGeodeticClotrollPoints: ''\n")
    configFile.write("FilenameExternalOrientation: '%s'\n" % os.path.join(projectDirectory,"eo.txt"))
    configFile.write("FilenameGeodeticMeasurements: ''\n")
    if baProblem.baSettings.placeRaportInProjectDirecotry:
        configFile.write("FilenameReport: '%s'\n" % os.path.join(projectDirectory, baProblem.baSettings.reportFileName))
    else:
        configFile.write("FilenameReport: '%s'\n" % os.path.join(baProblem.baSettings.reportDirectory, baProblem.baSettings.reportFileName))
    configFile.write("FilenameCalibrationCertificateData: ''\n")
    configFile.close()

def readBaSettings(filename):
    config = ba.BaSettings()
    reader = csv.reader(open(filename, 'r'), delimiter=' ')
    lines = []
    for line in reader:
        lines.append(line)
    
    elements = []
    for line in lines:
        for element in line:
            elements.append(element)
    
    print(elements)
    #reading loss function
    lossFunction = elements[elements.index("lossFunction:")+1]
    if lossFunction != "NONE" and lossFunction != "HUBER" and lossFunction != "CAUCHY": 
        print("ERROR! In sfmio.readBaSettings lossFunction should be \"NONE\" , \"HUBER\" or \"CAUCHY\",  but \"", lossFunction , "\" was given." )
        print("WARNING! In sfmio.readBaSettings setting the lossFunction to \"NONE\" and contiune processing." )
        lossFunction = "NONE"

    config.lossFunction = lossFunction

    #reading loss function parameter
    lossFunctionParameter = float(elements[elements.index("lossFunctionParameter:")+1])
    if lossFunctionParameter <= 0.0:
        print("ERROR! In sfmio.readBaSettings lossFunctionParameter must be > 0 but, but \"", lossFunctionParameter , "\" was given.")
        print("WARNING! In sfmio.readBaSettings setting lossFunctionParameter to \"1.5\" and contiune processing." )
        lossFunctionParameter = 1.5
    config.lossFunctionParameter = lossFunctionParameter

    config.noiseForImagePoints = float(elements[elements.index("noiseForImagePoints:")+1])

    idxNoiseControllPoints = elements.index("noiseForControllPoints:")
    idxNoiseExternalOrientation = elements.index("noiseForExternalOrientation:")

    diffOfIdx = idxNoiseExternalOrientation - idxNoiseControllPoints
    if (diffOfIdx - 1)%4 != 0:
        print("ERROR! In sfmio.readBaSettings Error in config file, after noiseForControllPoints:")
        print("ERROR! Failed to read config file!")

    for i in range(0,int(int((diffOfIdx - 1))/4) ):
        collectionId = int(elements[idxNoiseControllPoints + 1 + 4*i])
        standardDeviations = []
        standardDeviations.append(float(elements[idxNoiseControllPoints + 2 + 4*i]))
        standardDeviations.append(float(elements[idxNoiseControllPoints + 3 + 4*i]))
        standardDeviations.append(float(elements[idxNoiseControllPoints + 4 + 4*i]))
        config.noiseForControllPoints[collectionId] = standardDeviations

    diffOfIdx = len(elements) - idxNoiseExternalOrientation
    if (diffOfIdx - 1)%7 != 0:
       print("ERROR! In sfmio.readBaSettings Error in config file, after noiseForExternalOrientation:")
       print("ERROR! Failed to read config file!")

    for i in range(0,int(int((diffOfIdx - 1))/7) ):
        collectionId = int(elements[idxNoiseExternalOrientation + 1 + 7*i])
        standardDeviations = []
        for j in range(0,6):
            standardDeviations.append(float(elements[idxNoiseExternalOrientation + 2 + j + 7*i]))
        config.noiseForExternalOrientation[collectionId] = standardDeviations

    return config
