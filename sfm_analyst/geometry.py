import numpy as np
import conversions as conv
import scipy.spatial.transform as transf

class Range:
    def __init__(self, bottomLeft = np.array([0,0]), topRight = np.array([1,1])):
        self.bottomLeft = bottomLeft
        self.topRight = topRight
    
    def hasInside(self, x, y):
        if (x >= self.bottomLeft[0] and x <= self.topRight[0]):
            if (y >= self.bottomLeft[1] and y <= self.topRight[1]):
                return True
            else:
                return False
        else:
            return False
    
    def hasOtherRangeInside(self, otherRange):
        if not self.hasInside(otherRange.bottomLeft[0], otherRange.bottomLeft[1]):
            return False
        if not self.hasInside(otherRange.bottomLeft[0], otherRange.topRight[1]):
            return False
        if not self.hasInside(otherRange.topRight[0], otherRange.topRight[1]):
            return False
        if not self.hasInside(otherRange.topRight[0], otherRange.bottomLeft[1]):
            return False
        return True

    def getWidth(self):
        return self.topRight[0] - self.bottomLeft[0]

    def getHeight(self):
        return self.topRight[1] - self.bottomLeft[1]

    def print(self):
        print("range: left: ",self.bottomLeft[0]," right: ",self.topRight[0], " bottom: ", self.bottomLeft[1]," top: ", self.topRight[1])

    bottomLeft = np.array([0,0])
    topRight = np.array([1,1])

class Pose:
    def __init__(self, pos = np.zeros((3,1)), rot = np.eye(3) ):
        self.translation = pos
        self.rotation = rot
        self.__updateT()

    def __updateT(self):
        self.T = np.block([[self.rotation, self.translation],[np.zeros((1,3)), np.eye(1)]])

    def printme(self):
        print(self.x,self.y,self.z)

    def setRotationEuler(self,eulerAnglesRadians,sequence):
        rot = transf.Rotation.from_euler(sequence, eulerAnglesRadians, degrees = False)
        self.rotation = rot.as_matrix()
        self.__updateT()

    def setRotationQuaternion(self, quaternion):
        qn = conv.normalizeVector(quaternion)
        rot = transf.Rotation.from_quat(qn)
        self.rotation = rot.as_matrix()
        self.__updateT()

    def setRotationMatrix(self, rotationMatrix):
        self.rotation = rotationMatrix
        self.__updateT()

    def setTranslation(self, position):
        self.translation = position
        self.__updateT()

    def print(self):
        print("translation: ", self.translation)
        print("rotation: ", self.rotation)
        print("T: ", self.T)

    translation = np.zeros((3,1))# x, y, z coordinates
    rotation = np.eye(3) # rotation matrix
    stdDevTranslation =  np.array([0.01, 0.01, 0.01]) # std of x, y, z coordinates
    stdDevRotation  =  np.array([0.00175, 0.00175, 0.00175]) # roations about x, y, z axes in radians
    T = np.eye(4)


class PinholeCamera:
    def __updateFrustum(self):
        self.frustum = np.matrix(
            [[-0.5*self.width,0.5*self.width, 0.5*self.width, -0.5*self.width],
             [0.5*self.height,0.5*self.height, -0.5*self.height, -0.5*self.height],
             [self.cameraMatrix[0,0], self.cameraMatrix[0,0],self.cameraMatrix[0,0],self.cameraMatrix[0,0]],
              [1,1,1,1]])

    def __init__(self,*,name, pixelSizeMilimeters, numberOfRows, numberOfColumns, principalDistanceMilimeters ):
        self.name = name
        self.pixelSizeMilimeters = pixelSizeMilimeters
        principalDistancePixels = principalDistanceMilimeters / pixelSizeMilimeters
        self.height = numberOfRows
        self.width = numberOfColumns
        self.cameraMatrix = np.matrix([[-principalDistancePixels,0.0,0.0],[0.0,-principalDistancePixels,0.0],[0.0,0.0,1.0]])
        self.range = Range(np.array([-0.5*self.width,-0.5*self.height]), np.array([0.5*self.width,0.5*self.height])) 
        self.__updateFrustum()
    
    def setCalibrationFlags(self, flags):
        if len(flags) == 4:
            self.calibrationFlags = flags
        else:
            print("ERROR while setting calibraiton flags. Lenght of calibration flags is: ", len(flags), " while it should be 4.")

    def getViewingAnglesRadians(self): #does not take distortion into account
        return tuple((2.0* np.arctan(0.5*self.width/-self.cameraMatrix[0,0]), 2.0* np.arctan(0.5*self.height/-self.cameraMatrix[1,1])))

    def getViewingAnglesDegrees(self): #does not take distortion into account
        return tuple((360.0*np.arctan(0.5*self.width/-self.cameraMatrix[0,0])/np.pi, 360.0* np.arctan(0.5*self.height/-self.cameraMatrix[1,1])/np.pi))

    def getScaledFrustum(self, scale):
        scaledFrustum = np.copy(self.frustum)
        scaledFrustum[0:3,:] = scale*scaledFrustum[0:3,:]
        return scaledFrustum

    name = "unnamed_cmaera"
    calibrationFlags = [1,1,1,1]
    pixelSizeMilimeters = 0.006
    cameraMatrix = np.matrix([[-3300.0,0.0,0.0],[0.0,-3300.0,0.0],[0.0,0.0,1.0]])
    distortion = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    height = 4000
    width = 6000
    frustum = np.matrix([[-3000,3000,3000,-3000],[2000,2000,-2000,-2000],[-1650,-1650,-1650,-1650],[1,1,1,1]]) #4 X 4 matrix
    range = Range( np.array([-3000,-2000]),
                            np.array([3000,2000]) ) 

class Image:
    def setPose(self, p):
        self.pose = p

    def setCamera(self, camera):
        self.camera = camera
   
    rotationSequence = "xyz"
    camera = PinholeCamera(name = "default_camera", pixelSizeMilimeters = 0.006, numberOfRows = 6000, numberOfColumns = 4000, principalDistanceMilimeters = 20)
    pose = Pose()


class ImageCollection:

    def __init__(self,*, collectionId):
        self.id = collectionId

    def addImage(self, image, id):
        self.images[id] = image

    def getNumberOfImages(self):
        return len(self.images)
    
    id = 0
    observedPosition = False
    observedOrientation = False
    images = {}



class ObjectPointCollection:

    def __init__(self,*, collectionId):
        self.collectionId = collectionId

    def reserve(self, size):    
        self.coordinates = np.zeros((4,size))
        self.coordinates[3,:] = np.ones((1,size))
        self.standardDeviations = np.zeros((3,size)) 
        self.imagesIds = [[] for i in range(size)]
        self.types = ["tie" for i in range(size)]
        self.ids = [0 for i in range(size)]

    def insertPoint(self, x, y, z, stdDevX, stdDevY, stdDevZ, pointType, id, position):
        self.coordinates[0, position] = x
        self.coordinates[1, position] = y
        self.coordinates[2, position] = z
        self.standardDeviations[0, position] = stdDevX
        self.standardDeviations[1, position] = stdDevY
        self.standardDeviations[2, position] = stdDevZ
        self.ids[position] = id
        self.types[position] = pointType
        self.pointIdsToPositionMap[id] = position

    def removeLastNPoints(self, n):
        if n < self.coordinates.shape[1]:
            for i in range(0,n):
               self.ids.pop() 
               self.imagesIds.pop()
            coordinatesCopy = np.copy(self.coordinates[:,0:self.coordinates.shape[1] - n])
            self.coordinates = coordinatesCopy
    
    def getNumberOfPoints(self):
        return self.coordinates.shape[1]

    def getCombinedPointName(self, id):
        return str(self.collectionId) + "_" + str(self.ids[id])

    def clearImageIds(self):
        for imids in self.imagesIds:
            imids.clear()

    collectionId = 0
    coordinates = np.zeros((4,10))
    standardDeviations = np.ones((3,10))
    ids = [0 for i in range(10)]
    types = ["tie" for i in range(10)]
    imagesIds = [[] for i in range(10)] #list of tuples: (idOfImageCollection, idOfImage)
    pointIdsToPositionMap = {}
    

class Point2D:
    def __init__(self, x = 0.0, y = 0.0):
        self.x = x
        self.y = y    
    x = 0.0
    y = 0.0

class ObservationsInImages:
    def __init__(self):
        self.observations = []
    def add(self,idOfImageCollection, idOfImage, imagePoint:Point2D ):
        self.observations.append((idOfImageCollection, idOfImage, imagePoint))
    def getNumberOfPoints(self):
        return len(self.observations)


class ImagePoint:
    def __init__(self, x, y, idOfImageCollection, idOfImage, idOfObjectPointCollection, idOfObjectPoint):
        self.observation = Point2D(x,y)
        self.idOfImageCollection = idOfImageCollection
        self.idOfImage = idOfImage
        self.idOfObjectPointCollection = idOfObjectPointCollection
        self.idOfObjectPoint = idOfObjectPoint
    
    def getCombinedPointName(self):
        return str(self.idOfObjectPointCollection) + "_" + str(self.idOfObjectPoint)
    
    def getCombinedImageName(self):
        return str(self.idOfImageCollection) + "_" + str(self.idOfImage)

    observation = Point2D()
    projection = Point2D()
    idOfImageCollection = 0
    idOfImage = 0
    idOfObjectPointCollection = 0
    idOfObjectPoint = 0
    
    


def projectObjectPointCollectionToImage(image, objectPointCollection, idStart, idEnd ):
    selectedObjectPoints = objectPointCollection.coordinates[:, idStart:idEnd]
    return  project(image, selectedObjectPoints)


def project(image: Image, objectPoints: np.ndarray) -> np.ndarray:
    #calculating pose that is used for projection
    #translation = np.matmul(image.pose.rotation, -image.pose.translation)
    #pose = Pose(translation, image.pose.rotation)

    TI = np.array([[1,0,0,0],[0,1,0,0],[0,0,1,0]])
    objectPointsInCameraFrame = np.matmul(TI,np.matmul(np.linalg.inv(image.pose.T), objectPoints))
    projectedImagePoints = np.matmul(image.camera.cameraMatrix,objectPointsInCameraFrame) #homogenous
    projectedImagePoints[0,:] =np.divide(projectedImagePoints[0,:],projectedImagePoints[2,:]) #in pixels
    projectedImagePoints[1,:] =np.divide(projectedImagePoints[1,:],projectedImagePoints[2,:]) #in pixels
    projectedImagePoints[2,:] =np.ones((1,projectedImagePoints.shape[1]) ) #in pixels
    return projectedImagePoints

def computeMultiVeiwIntersection(observations: ObservationsInImages, imageCollections : list[ImageCollection] ):
    numberOfPoints = observations.getNumberOfPoints()
    A = np.zeros((2*numberOfPoints,3))
    L = np.zeros((2*numberOfPoints,1))
    for i in range(0,numberOfPoints):
        observation = observations.observations[i]
        image = imageCollections[observation[0]].images[observation[1]]
        R = image.pose.rotation
        p = image.pose.translation
        c = -image.camera.cameraMatrix[0,0]

        x = observation[2].x/c
        y = observation[2].y/c

        A[2*i,:] = np.transpose(x*R[:,2] + R[:,0])
        A[2*i+1,:] = np.transpose(y*R[:,2] + R[:,1])

        #A[2*i,0] = x*R[0,2]  + R[0,0]
        #A[2*i,1] = x*R[1,2]  + R[1,0]
        #A[2*i,2] = x*R[2,2]  + R[2,0]
        #
        #A[2*i+1,0] = y*R[0,2]  + R[0,1]
        #A[2*i+1,1] = y*R[1,2]  + R[1,1]
        #A[2*i+1,2] = y*R[2,2]  + R[2,1]

        L[2*i] = A[2*i,0]*p[0] + A[2*i,1]*p[1] + A[2*i,2]*p[2]  
        L[2*i+1] = A[2*i+1,0]*p[0] + A[2*i+1,1]*p[1] + A[2*i+1,2]*p[2]

    #AT = np.transpose(A)
    #ATA = np.matmul(AT,A)
    #Q = np.linalg.inv(ATA)
    #ATL = np.matmul(AT,L)
    #objectPointCoordinates = np.matmul(Q,ATL)
    leastSquareSolution = np.linalg.lstsq(A,L,rcond = None)

    return leastSquareSolution[0]
  
    