import numpy as np
from numpy.random import Generator
import geometry
import copy

class StructGenConfig:

    def __init__(self, cellSize = 10.0, pointsPerCell = 5, dispersion = 4.0, standardDeviation = np.array([0.02, 0.02, 0.03]) , approach = "uniform", typeOfPoints = "tie"):
        self.cellSize = cellSize
        self.pointsPerCell = pointsPerCell
        self.dispersion = dispersion
        self.standardDeviation = standardDeviation

        if (typeOfPoints == "tie" or typeOfPoints == "control" or typeOfPoints == "check"):
            self.typeOfPoints = typeOfPoints
        else:
            print("WARNING! In sgen.StuctGenConfig::__init__ typeOfPoints should be \"tie\" , \"control\" or \"check\",  but \" ", typeOfPoints , "\" type given." )
            print("WARNING! In sgen.StuctGenConfig::__init__ setting the typeOfPoints to \"tie\" and contiune processing." )
            self.typeOfPoints = "tie"

        if (approach == "uniform" or approach == "gaussian"):
            self.approach = approach
        else:
            print("WARNING! In sgen.StuctGenConfig::__init__ approach should be \"uniform\" or \"gaussian\", but \" ", approach , "\" was given." )
            print("WARNING! In sgen.StuctGenConfig::__init__ setting the approach to \"uniform\" and contiune processing." )
            self.approach = "uniform"

    cellSize = 10.0
    pointsPerCell = 5
    dispresion = 4.0
    standardDeviation = np.array([0.02, 0.02, 0.03])
    typeOfPoints = "tie" #tie, control, check
    approach = "uniform" #uniform or gausssian


def generateProcessingRangeFromImages(rasterioDsm, listOfImageCollections = []):
    
    model = rasterioDsm.read()
    if (len(model.shape) == 3):
        model = model[0,:,:]
    print(model.shape)
    print(rasterioDsm.meta)
    print(rasterioDsm.meta["transform"])
    coordinateTransform = rasterioDsm.meta["transform"]
    mask = model == rasterioDsm.meta['nodata']
    maskedModel = np.ma.masked_array(model, mask)
    lowestHeight = maskedModel.min()

    dsmRange = geometry.Range( np.array([rasterioDsm.bounds.left,rasterioDsm.bounds.bottom]),
                               np.array([rasterioDsm.bounds.right,rasterioDsm.bounds.top]) )  

    numberOfAllImages = 0;
    for imageCollection in listOfImageCollections:
        numberOfAllImages += len(imageCollection.images)
    
    intersections = np.zeros((4*numberOfAllImages,2))
    lineId = 0
    #for each image we calculate the intersection of furstum with plan Z = lowestHeight
    for imageCollection in listOfImageCollections:
        for key, image in imageCollection.images.items():
            frustum = np.matmul(image.pose.T, image.camera.getScaledFrustum(image.camera.pixelSizeMilimeters*0.001))[0:3,:]
            for col in range(0,4):
                for row in range(0,3):
                    frustum[row,col] = frustum[row,col] - image.pose.translation[row,0]
            #intersecting linen with plane
            for col in range(0,4):
                t = (lowestHeight - image.pose.translation[2,0])/frustum[2,col]
                intersections[lineId,0] = image.pose.translation[0,0] + t*frustum[0,col]
                intersections[lineId,1] = image.pose.translation[1,0] + t*frustum[1,col]
                lineId = lineId+1

    bottomLeft = np.array([np.min(intersections[:,0]), np.min(intersections[:,1])] )
    topRight = np.array([np.max(intersections[:,0]), np.max(intersections[:,1])] )  
    outputRange = geometry.Range(bottomLeft, topRight)

    if not dsmRange.hasOtherRangeInside(outputRange):
        print("WARNIG in generateProcessingRangeFromImages: image range is outside or intersects dsmRange.")

    return outputRange


def generateUsingSurfaceModel(rasterioDsm, generationConfig = StructGenConfig(), givenRange = geometry.Range(),  id = 0):

    #generation of structure based on givenRange and dsm:
    #generating list of geometry.Range for the whole dsm range:

    dsmRange = geometry.Range( np.array([rasterioDsm.bounds.left,rasterioDsm.bounds.bottom]),
                               np.array([rasterioDsm.bounds.right,rasterioDsm.bounds.top]) )  

    print("processing range of size DX = ", givenRange.getWidth(), " DY = ",givenRange.getHeight(),  " created.")

    cols = int(np.floor(givenRange.getWidth()/generationConfig.cellSize)) + int(1)
    rows = int(np.floor(givenRange.getHeight()/generationConfig.cellSize)) + int(1)

    print("generating structure in ",cols*rows , " cells...")
    sgenCells = []

    for row in range(0,rows):
        for col in range(0, cols):
            newRange = geometry.Range() 
            newRange.bottomLeft[0] = givenRange.bottomLeft[0] + col*generationConfig.cellSize
            newRange.bottomLeft[1] = givenRange.bottomLeft[1] + row*generationConfig.cellSize
            newRange.topRight[0] = newRange.bottomLeft[0] + generationConfig.cellSize
            newRange.topRight[1] = newRange.bottomLeft[1] + generationConfig.cellSize
            sgenCells.append(copy.deepcopy(newRange))
    
    randomNumberGenerator =  np.random.default_rng()
    objectPointCollection = geometry.ObjectPointCollection(collectionId = 0)
    maxPossibleNumberOfPoints = cols * rows * generationConfig.pointsPerCell
    objectPointCollection.reserve(maxPossibleNumberOfPoints)

    print("processing range: ")
    givenRange.print()
    print("dsm range: ")
    dsmRange.print()
 
    pointPosition = 0
    numberOfAddedPoints = 0
    xvals = np.zeros((5,))
    yvals = np.zeros((5,))
    for cell in sgenCells:
        if generationConfig.approach == "uniform":
            xvals = randomNumberGenerator.uniform(cell.bottomLeft[0], cell.topRight[0], generationConfig.pointsPerCell)
            yvals = randomNumberGenerator.uniform(cell.bottomLeft[1], cell.topRight[1], generationConfig.pointsPerCell)   
        if generationConfig.approach == "gaussian":
            centerx = randomNumberGenerator.uniform(cell.bottomLeft[0], cell.topRight[0], 1)
            centery = randomNumberGenerator.uniform(cell.bottomLeft[1], cell.topRight[1], 1)
            xvals = randomNumberGenerator.normal(centerx[0], generationConfig.dispersion, generationConfig.pointsPerCell)
            yvals = randomNumberGenerator.normal(centery[0], generationConfig.dispersion, generationConfig.pointsPerCell)   
        for x, y in zip(xvals.tolist(), yvals.tolist()):
            if givenRange.hasInside(x , y) and dsmRange.hasInside(x,y):
                sampledHeight = list(rasterioDsm.sample([(x,y)]))[0][0]
                if sampledHeight != rasterioDsm.meta['nodata']:
                    objectPointCollection.insertPoint(x, y, sampledHeight,
                                                      generationConfig.standardDeviation[0], generationConfig.standardDeviation[1], generationConfig.standardDeviation[2],
                                                      generationConfig.typeOfPoints, pointPosition, pointPosition)
                    pointPosition = pointPosition + 1
                    numberOfAddedPoints = numberOfAddedPoints + 1
    
    objectPointCollection.removeLastNPoints(maxPossibleNumberOfPoints-numberOfAddedPoints)
    objectPointCollection.collectionId = id
    return objectPointCollection

#def readFromTexfile(filename):