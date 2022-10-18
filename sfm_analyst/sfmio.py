import geometry
import numpy as np
import conversions as conv

class Camera3DModel:

    def __init__(self,*,frustumVertices,axesVertices,normalVectors, perspectiveCenter, idsOfFrustumVertices, idsOfNormalVectors):
        self.frustumVertices = frustumVertices
        self.axesVertices = axesVertices
        self.normalVectors = normalVectors
        self.perspectiveCenter = perspectiveCenter
        self.idsOfFrustumVertices = idsOfFrustumVertices
        self.idsOfNormalVectors = idsOfNormalVectors
            
    frustumVertices = np.zeros((3,5))
    axesVertices = np.eye(3)
    normalVectors = np.zeros((3,5))
    perspectiveCenter = np.zeros((3,1))
    idsOfFrustumVertices = np.arange(0,5,1)
    idsOfNormalVectors = np.arange(0,5,1)


def writeMaterials(filename):
    objFile = open(filename,"w")
    objFile.write("newmtl colorRed\n")
    objFile.write("Kd 1.000 0.000 0.000\n")
    objFile.write("\n")
    objFile.write("newmtl colorGreen\n")
    objFile.write("Kd 0.000 1.000 0.000\n")
    objFile.write("\n")
    objFile.write("newmtl colorBlue\n")
    objFile.write("Kd 0.000 0.000 1.000\n")

    objFile.close()

def writeImageCollectionToObj(imageCollection, filename,* , imageWidthInMeters, axesLenghtInMeters):
    writeMaterials("materials.mtl")
    
    objFilename = filename + ".obj"
    dxfFilename = filename + "_axes.dxf"
    
    imageId = 0
    
    camera3DModels = {}

    for key, value in imageCollection.images.items():
        frustumInWorldFrameMeters = np.matmul(value.pose.T, value.camera.getScaledFrustum(imageWidthInMeters/value.camera.width))
        #we are adding stacking horizontally projection center to the frustum, so we will have 5 points to draw the camera: 
        frustumAndProjectionCenterInWorldFrameMeters = np.block([frustumInWorldFrameMeters[0:3,:], value.pose.translation] )
        cameraAxisVectorInWorldFrameMeters = np.matmul(value.pose.rotation, np.matrix([[0.0],[0.0],[value.camera.cameraMatrix[0,0]]]))
        #we need frustum vertices in camera frame resolved in wrold frame to calculate normal vectors
        #TODO: we rather don't need to subratract translation because this does not change the cross product
        frustumVertices = np.copy(frustumInWorldFrameMeters[0:3,0:4])
        for i in range(0,4):
            for j in range(0,3):
                frustumVertices[j,i] = frustumVertices[j,i] - value.pose.translation[j,0]
        
        normalVectors = np.zeros((3,5))
        #calculating cross products of frustum faces           
        normalVectors[:,0] = conv.normalizeVector(np.cross(frustumVertices[:,1], frustumVertices[:,0]))
        normalVectors[:,1] = conv.normalizeVector(np.cross(frustumVertices[:,2], frustumVertices[:,1]))
        normalVectors[:,2] = conv.normalizeVector(np.cross(frustumVertices[:,3], frustumVertices[:,2]))
        normalVectors[:,3] = conv.normalizeVector(np.cross(frustumVertices[:,0], frustumVertices[:,3]))
        normalVectors[:,4] = conv.normalizeVector(cameraAxisVectorInWorldFrameMeters).reshape(3,)
        axesVertices = np.copy( value.pose.rotation)
        for i in range(0,3):
            for j in range(0,3):
                axesVertices[i,j] = axesLenghtInMeters * axesVertices[i,j] + value.pose.translation[i,0] 
        
        listOfIdsOfFrustumVertices = np.arange(5*imageId+1, 5*imageId+6, 1)
        listOfIdsOfNormalVectors = np.arange(5*imageId+1, 5*imageId+6, 1)
        camera3DModel = Camera3DModel(frustumVertices = frustumAndProjectionCenterInWorldFrameMeters,
                                      axesVertices = axesVertices,
                                      normalVectors =  normalVectors,
                                      perspectiveCenter = value.pose.translation,
                                      idsOfFrustumVertices = listOfIdsOfFrustumVertices,
                                      idsOfNormalVectors = listOfIdsOfNormalVectors)

        camera3DModels[key] = camera3DModel

        imageId = imageId+1

    objFile = open(objFilename,"w")    
    objFile.write("mtllib materials.mtl\n")
    #printing vertices
    objFile.write("\n#vertices\n")

    for key, camModel in camera3DModels.items():
        objFile.write("v %.5f %.5f %.5f\n" % (camModel.frustumVertices[0,0], camModel.frustumVertices[1,0], camModel.frustumVertices[2,0])) 
        objFile.write("v %.5f %.5f %.5f\n" % (camModel.frustumVertices[0,1], camModel.frustumVertices[1,1], camModel.frustumVertices[2,1])) 
        objFile.write("v %.5f %.5f %.5f\n" % (camModel.frustumVertices[0,2], camModel.frustumVertices[1,2], camModel.frustumVertices[2,2])) 
        objFile.write("v %.5f %.5f %.5f\n" % (camModel.frustumVertices[0,3], camModel.frustumVertices[1,3], camModel.frustumVertices[2,3])) 
        objFile.write("v %.5f %.5f %.5f\n" % (camModel.frustumVertices[0,4], camModel.frustumVertices[1,4], camModel.frustumVertices[2,4])) 

    objFile.write("\n#normal vectors\n")
    #printing normal vectors
    for key, camModel in camera3DModels.items():
        objFile.write("vn %.7f %.7f %.7f\n" % (camModel.normalVectors[0,0], camModel.normalVectors[1,0], camModel.normalVectors[2,0])  )
        objFile.write("vn %.7f %.7f %.7f\n" % (camModel.normalVectors[0,1], camModel.normalVectors[1,1], camModel.normalVectors[2,1])  )
        objFile.write("vn %.7f %.7f %.7f\n" % (camModel.normalVectors[0,2], camModel.normalVectors[1,2], camModel.normalVectors[2,2])  )
        objFile.write("vn %.7f %.7f %.7f\n" % (camModel.normalVectors[0,3], camModel.normalVectors[1,3], camModel.normalVectors[2,3])  )
        objFile.write("vn %.7f %.7f %.7f\n" % (camModel.normalVectors[0,4], camModel.normalVectors[1,4], camModel.normalVectors[2,4])  )
    
    objFile.write("\n#cameras\n")
    #drawing faces in obj file:
    for key, c in camera3DModels.items():
        objFile.write("o camera frustum %s\n" % (key))
        objFile.write("f %d//%d %d//%d %d//%d\n" % (c.idsOfFrustumVertices[0], c.idsOfNormalVectors[0], c.idsOfFrustumVertices[4], c.idsOfNormalVectors[0], c.idsOfFrustumVertices[1], c.idsOfNormalVectors[0] ))
        objFile.write("f %d//%d %d//%d %d//%d\n" % (c.idsOfFrustumVertices[1], c.idsOfNormalVectors[1], c.idsOfFrustumVertices[4], c.idsOfNormalVectors[1], c.idsOfFrustumVertices[2], c.idsOfNormalVectors[1] ))
        objFile.write("f %d//%d %d//%d %d//%d\n" % (c.idsOfFrustumVertices[2], c.idsOfNormalVectors[2], c.idsOfFrustumVertices[4], c.idsOfNormalVectors[2], c.idsOfFrustumVertices[3], c.idsOfNormalVectors[2] ))
        objFile.write("f %d//%d %d//%d %d//%d\n" % (c.idsOfFrustumVertices[3], c.idsOfNormalVectors[3], c.idsOfFrustumVertices[4], c.idsOfNormalVectors[3], c.idsOfFrustumVertices[0], c.idsOfNormalVectors[3] ))
        objFile.write("f %d//%d %d//%d %d//%d %d//%d\n" % (c.idsOfFrustumVertices[0], c.idsOfNormalVectors[4], c.idsOfFrustumVertices[1], c.idsOfNormalVectors[4], c.idsOfFrustumVertices[2], c.idsOfNormalVectors[4], c.idsOfFrustumVertices[3] , c.idsOfNormalVectors[4] ))
    objFile.close()

    dxfFile = open(dxfFilename,"w")
    dxfFile.write("0\n")
    dxfFile.write("SECTION\n")
    dxfFile.write("2\n")
    dxfFile.write("HEADER\n")
    dxfFile.write("9\n")
    dxfFile.write("$ACADVER\n")
    dxfFile.write("1\n")
    dxfFile.write("AC1009\n")
    dxfFile.write("0\n")
    dxfFile.write("ENDSEC\n")
    dxfFile.write("0\n")
    dxfFile.write("SECTION\n")
    dxfFile.write("2\n")
    dxfFile.write("ENTITIES\n")
    dxfFile.write("0\n")


    for key, camModel in camera3DModels.items():
        dxfFile.write("LINE\n")
        dxfFile.write("8\n")
        dxfFile.write("0\n")
        dxfFile.write("62\n")
        dxfFile.write("1\n")
        dxfFile.write("10\n")
        dxfFile.write("%.5f\n" % (camModel.perspectiveCenter[0,0]))
        dxfFile.write("20\n")
        dxfFile.write("%.5f\n" % (camModel.perspectiveCenter[1,0]))
        dxfFile.write("30\n")
        dxfFile.write("%.5f\n" % (camModel.perspectiveCenter[2,0]))
        dxfFile.write("11\n")
        dxfFile.write("%.5f\n" % (camModel.axesVertices[0,0]))
        dxfFile.write("21\n")
        dxfFile.write("%.5f\n" % (camModel.axesVertices[1,0]))
        dxfFile.write("31\n")
        dxfFile.write("%.5f\n" % (camModel.axesVertices[2,0]))
        dxfFile.write("0\n")

        dxfFile.write("LINE\n")
        dxfFile.write("8\n")
        dxfFile.write("0\n")
        dxfFile.write("62\n")
        dxfFile.write("100\n")
        dxfFile.write("10\n")
        dxfFile.write("%.5f\n" % (camModel.perspectiveCenter[0,0]))
        dxfFile.write("20\n")
        dxfFile.write("%.5f\n" % (camModel.perspectiveCenter[1,0]))
        dxfFile.write("30\n")
        dxfFile.write("%.5f\n" % (camModel.perspectiveCenter[2,0]))
        dxfFile.write("11\n")
        dxfFile.write("%.5f\n" % (camModel.axesVertices[0,1]))
        dxfFile.write("21\n")
        dxfFile.write("%.5f\n" % (camModel.axesVertices[1,1]))
        dxfFile.write("31\n")
        dxfFile.write("%.5f\n" % (camModel.axesVertices[2,1]))
        dxfFile.write("0\n")

        dxfFile.write("LINE\n")
        dxfFile.write("8\n")
        dxfFile.write("0\n")
        dxfFile.write("62\n")
        dxfFile.write("4\n")
        dxfFile.write("10\n")
        dxfFile.write("%.5f\n" % (camModel.perspectiveCenter[0,0]))
        dxfFile.write("20\n")
        dxfFile.write("%.5f\n" % (camModel.perspectiveCenter[1,0]))
        dxfFile.write("30\n")
        dxfFile.write("%.5f\n" % (camModel.perspectiveCenter[2,0]))
        dxfFile.write("11\n")
        dxfFile.write("%.5f\n" % (camModel.axesVertices[0,2]))
        dxfFile.write("21\n")
        dxfFile.write("%.5f\n" % (camModel.axesVertices[1,2]))
        dxfFile.write("31\n")
        dxfFile.write("%.5f\n" % (camModel.axesVertices[2,2]))
        dxfFile.write("0\n")
    
    dxfFile.write("ENDSEC\n")
    dxfFile.write("0\n")
    dxfFile.close()


def importFromExternalOrientationTextfile(filename, delimiter, imageCollection, rotationSequence, observedPosition, observedOrientation, camera):
    poses = np.loadtxt(filename, dtype =str, delimiter = delimiter, skiprows = 1)
    imageCollection.observedPosition = observedPosition
    imageCollection.observedOrientation = observedOrientation
    for row in range(0, poses.shape[0]):
        id = poses[row,0];
        translation = np.zeros((3,1))
        eulerAngles = np.zeros(3)
        translation[0,0] = float(poses[row,1])
        translation[1,0] = float(poses[row,2])
        translation[2,0] = float(poses[row,3])
        eulerAngles[0] = float(poses[row,4])
        eulerAngles[1] = float(poses[row,5])
        eulerAngles[2] = float(poses[row,6])
        pose = geometry.Pose()
        pose.setRotationEuler(conv.degrees2Radians(eulerAngles),rotationSequence)
        pose.setTranslation(translation)
        image = geometry.Image()
        image.setPose(pose)
        image.setCamera(camera)
        image.rotationSequence = rotationSequence
        imageCollection.addImage(image,id)



def writeObjectPointsToFile(filename, objectPointCollection):
    typeToIdMap = {"tie" : 0, "control" : 3, "check" : 4}
    npoints = objectPointCollection.getNumberOfPoints()
    file = open(filename,"w")    
    for i in range(0,npoints):
        file.write("%s " % objectPointCollection.getCombinedPointName(i) )
        file.write("%.5f %.5f %.5f " % (objectPointCollection.coordinates[0,i], objectPointCollection.coordinates[1,i], objectPointCollection.coordinates[2,i]))
        file.write("%d " % typeToIdMap[objectPointCollection.types[i]])
        file.write("%.5f %.5f %.5f\n" % (objectPointCollection.standardDeviations[0,i], objectPointCollection.standardDeviations[1,i], objectPointCollection.standardDeviations[2,i]))
    file.close()


def writeSurfaceModelToObj(filename, rasterioDsm, givenRange):
    dsmRange = geometry.Range( np.array([rasterioDsm.bounds.left,rasterioDsm.bounds.bottom]),
                               np.array([rasterioDsm.bounds.right,rasterioDsm.bounds.top]) ) 

    if not dsmRange.hasOtherRangeInside(givenRange):
        print("ERROR in writeSurfaceModelToObj: export range intersects or is outside the processing range.")
    else:
        fileObj = open(filename,"w")
        
        dsmData = rasterioDsm.read(1).astype(float)
        print(dsmData.shape)

        (c1,r1) = ~rasterioDsm.transform*(givenRange.bottomLeft[0], givenRange.bottomLeft[1])
        (c2,r2) = ~rasterioDsm.transform*(givenRange.topRight[0], givenRange.topRight[1])

        cmin = 0
        cmax = 0
        rmin = 0
        rmax = 0

        if c1 < c2:
            cmin = int(np.floor(c1))
            cmax = int(np.ceil(c2))
        else:
            cmin = int(np.floor(c2))
            cmax = int(np.ceil(c1))
        
        if r1 < r2:
            rmin = int(np.floor(r1))
            rmax = int(np.ceil(r2))
        else:
            rmin = int(np.floor(r2))
            rmax = int(np.ceil(r1))

        if rmin < 0:
            rmin = 0

        if cmin < 0:
            cmin = 0

        if rmax > dsmData.shape[0]-1:
            rmax = dsmData.shape[0]-1 
        
        if cmax > dsmData.shape[1]-1:
            cmax = dsmData.shape[1]-1

        print("range of the dsm to export: columns: ", cmin, cmax, " rows: ", rmin, rmax)

        numberOfCols = cmax - cmin + 1 

        #writing vertices to obj
        fileObj.write("#vertices\n")
        validVertexId = 0 #vertices that have data

        mapVertexIdToIsValid = {}
        mapVertexIdToValidVertexId = {}
        mapValidVertexIdToCoords = {}

        #getting vertices
        for row in range(rmin,rmax+1):
            rowId = row - rmin
            for col in range(cmin, cmax+1):
                colId = col - cmin
                vertexId = rowId * numberOfCols + colId
                (x,y) =  rasterioDsm.transform*(col,row)
                #z = list(rasterioDsm.sample([(x,y)]))[0][0]
                z = dsmData[row, col]
                if z == rasterioDsm.meta['nodata']:
                    mapVertexIdToIsValid[vertexId] = False
                else:
                    mapVertexIdToIsValid[vertexId] = True
                    mapVertexIdToValidVertexId[vertexId] = validVertexId
                    mapValidVertexIdToCoords[validVertexId] = (x,y,z)
                    fileObj.write("v %.4f %.4f %.4f\n" % (x, y, z))
                    validVertexId = validVertexId + 1
        
        listOfVertices = []
        listOfNormalVectors = []
        #getting ids for faces
        for row in range(rmin,rmax):
            rowId = row - rmin
            for col in range(cmin, cmax):
                colId = col - cmin
                #for each point we have to write up to two faces
                vertexId1 = rowId * numberOfCols + colId
                if mapVertexIdToIsValid[vertexId1] == False:
                    break
                vertexId2 = rowId * numberOfCols + colId + 1
                vertexId3 = (rowId + 1) * numberOfCols + colId + 1
                if mapVertexIdToIsValid[vertexId3] == False:
                    break
                vertexId4 = (rowId + 1) * numberOfCols + colId
                #face 1-4-3-1
                if mapVertexIdToIsValid[vertexId4] == True:
                    listOfVertices.append((vertexId1, vertexId4, vertexId3))
                    #calculation of normal vector
                    idValidVertex1 = mapVertexIdToValidVertexId[vertexId1]
                    idValidVertex4 = mapVertexIdToValidVertexId[vertexId4]
                    idValidVertex3 = mapVertexIdToValidVertexId[vertexId3]
                    (x1, y1, z1) = mapValidVertexIdToCoords[idValidVertex1]
                    (x4, y4, z4) = mapValidVertexIdToCoords[idValidVertex4]
                    (x3, y3, z3) = mapValidVertexIdToCoords[idValidVertex3]
                    v1 = np.array([x1,y1,z1])
                    v4 = np.array([x4,y4,z4])
                    v3 = np.array([x3,y3,z3])
                    v14 = v4 - v1
                    v13 = v3 - v1
                    listOfNormalVectors.append(conv.normalizeVector(np.cross(v14,v13)))
                #face 1-3-2-1
                if mapVertexIdToIsValid[vertexId2] == True:
                    listOfVertices.append((vertexId1, vertexId3, vertexId2))
                    #calculation of normal vector
                    idValidVertex1 = mapVertexIdToValidVertexId[vertexId1]
                    idValidVertex3 = mapVertexIdToValidVertexId[vertexId3]
                    idValidVertex2 = mapVertexIdToValidVertexId[vertexId2]
                    (x1, y1, z1) = mapValidVertexIdToCoords[idValidVertex1]
                    (x3, y3, z3) = mapValidVertexIdToCoords[idValidVertex3]
                    (x2, y2, z2) = mapValidVertexIdToCoords[idValidVertex2]
                    v1 = np.array([x1,y1,z1])
                    v3 = np.array([x3,y3,z3])
                    v2 = np.array([x2,y2,z2])
                    v13 = v3 - v1
                    v12 = v2 - v1
                    listOfNormalVectors.append(conv.normalizeVector(np.cross(v13,v12)))

        #writing faces and normal vectors to obj file
        fileObj.write("\n#normal vectors\n")
        for nv in listOfNormalVectors:
            fileObj.write("vn %.4f %.4f %.4f\n" % (nv[0], nv[1], nv[2]))
        
        fileObj.write("\n#faces\n")
        normalVectorId = 1
        for face in listOfVertices:
            fileObj.write("f %d//%d %d//%d %d//%d\n" % (face[0]+1, normalVectorId, face[1]+1, normalVectorId, face[2]+1, normalVectorId))
            normalVectorId = normalVectorId + 1
        fileObj.close()

def writeRaysToDxf(filename, objectPointsCollections, imageCollections, pointType, colorId):
    dxfFile = open(filename,"w")
    dxfFile.write("0\n")
    dxfFile.write("SECTION\n")
    dxfFile.write("2\n")
    dxfFile.write("HEADER\n")
    dxfFile.write("9\n")
    dxfFile.write("$ACADVER\n")
    dxfFile.write("1\n")
    dxfFile.write("AC1009\n")
    dxfFile.write("0\n")
    dxfFile.write("ENDSEC\n")
    dxfFile.write("0\n")
    dxfFile.write("SECTION\n")
    dxfFile.write("2\n")
    dxfFile.write("ENTITIES\n")
    dxfFile.write("0\n")

    for pointCollection in objectPointsCollections:
        for pointIdx in range(0, pointCollection.getNumberOfPoints()):
            if len(pointCollection.imagesIds[pointIdx]) < 2 and pointCollection.types[pointIdx] == "tie":
                continue
            if len(pointCollection.imagesIds[pointIdx]) < 2 and pointCollection.types[pointIdx] == "check":
                continue
            if pointCollection.types[pointIdx] == pointType:
                for (idOfImageCollection, idOfImage) in pointCollection.imagesIds[pointIdx]:
                    x0 = imageCollections[idOfImageCollection].images[idOfImage].pose.translation[0,0]
                    y0 = imageCollections[idOfImageCollection].images[idOfImage].pose.translation[1,0]
                    z0 = imageCollections[idOfImageCollection].images[idOfImage].pose.translation[2,0]
                    dxfFile.write("LINE\n")
                    dxfFile.write("8\n")
                    dxfFile.write("0\n")
                    dxfFile.write("62\n")
                    dxfFile.write(str(colorId) + "\n")
                    dxfFile.write("10\n")
                    dxfFile.write("%.5f\n" % (x0))
                    dxfFile.write("20\n")
                    dxfFile.write("%.5f\n" % (y0))
                    dxfFile.write("30\n")
                    dxfFile.write("%.5f\n" % (z0))
                    dxfFile.write("11\n")
                    dxfFile.write("%.5f\n" % (pointCollection.coordinates[0, pointIdx]))
                    dxfFile.write("21\n")
                    dxfFile.write("%.5f\n" % (pointCollection.coordinates[1, pointIdx]))
                    dxfFile.write("31\n")
                    dxfFile.write("%.5f\n" % (pointCollection.coordinates[2, pointIdx]))
                    dxfFile.write("0\n")

    dxfFile.write("ENDSEC\n")
    dxfFile.write("0\n")
    dxfFile.close()

