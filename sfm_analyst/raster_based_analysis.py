from asyncio import proactor_events
import re
import numpy as np
import geometry
import rasterio
import multiprocessing
import rasterio_tools
import copy as cp
import time


def computeImageOverlap(*,rasterioDsm: rasterio.DatasetReader,
                    listOfImageCollections: list[geometry.ImageCollection]) -> tuple[np.ndarray, dict[(int,int), geometry.ObservationsInImages] ]:
    model = rasterioDsm.read()
    if (len(model.shape) == 3):
        model = model[0,:,:]

    overlapMap = np.zeros(model.shape)
    imageObservationsOfDSM = {}

    coordinatesOfDSMPoints = rasterio_tools.raster2Array(rasterioDsm = rasterioDsm)

    whereNodata = np.where(coordinatesOfDSMPoints[2,:] == rasterioDsm.meta["nodata"])[0]
    coordinatesOfDSMPoints = np.delete(coordinatesOfDSMPoints, whereNodata, axis = 1)

    nRows = model.shape[0]
    nCols = model.shape[1]
    numberOfPoints = nRows*nCols
    xGrid, yGrid = np.meshgrid(range(0,nCols),range(0,nRows))
    rowColCoordinates = np.reshape(np.dstack((yGrid,xGrid)),(numberOfPoints,2))

    rowColCoordinates = np.delete(rowColCoordinates, whereNodata, axis = 0)

    print("projecting")

    for imageCollection in listOfImageCollections:
        for imageId, image in imageCollection.images.items():
            
            imagePoints = geometry.project(image,coordinatesOfDSMPoints)
            x = imagePoints[0,:]
            y = imagePoints[1,:]
            w = image.camera.width
            h = image.camera.height
            whereInsideImage = np.logical_and(np.logical_and(x < w/2, x > -w/2),np.logical_and(y < h/2, y > -h/2))
            rowColIdsWhereVisible = rowColCoordinates[whereInsideImage.tolist()[0],:]
            overlapMap[rowColIdsWhereVisible[:,0],rowColIdsWhereVisible[:,1]]+=1

            projectedDSM = imagePoints[0:2,whereInsideImage.tolist()[0]]
            sizeOfProjectedDSM = projectedDSM.shape[1]
            print("imageId: ",imageId, " projected grid size:  ", sizeOfProjectedDSM)

            for i in range(0,sizeOfProjectedDSM):
                rowId = rowColIdsWhereVisible[i,0]
                colId = rowColIdsWhereVisible[i,1]
                if (rowId,colId) not in imageObservationsOfDSM.keys():
                    imageObservationsOfDSM[(rowId,colId)] = geometry.ObservationsInImages()
                imageObservationsOfDSM[(rowId,colId)].add(imageCollection.id ,imageId, geometry.Point2D(projectedDSM[0,i],projectedDSM[1,i]))
            

    return overlapMap, imageObservationsOfDSM


def projectDSMToImages(processId: int, shapeOfRaster, coordinatesOfDSMPoints, rowColCoordinates, listOfImageData):
    
    overlapMap = np.zeros(shapeOfRaster, dtype = int)
    imageObservationsOfDSM = {}

    for imageData in listOfImageData:
        imageCollectionId = imageData[0][0]
        imageId = imageData[0][1]
        image = imageData[1]

        print(f"in projectDSMToImages process {processId}, projecting to image {imageId} in collection {imageCollectionId}")
            
        imagePoints = geometry.project(image,coordinatesOfDSMPoints)
        x = imagePoints[0,:]
        y = imagePoints[1,:]
        w = image.camera.width
        h = image.camera.height
        whereInsideImage = np.logical_and(np.logical_and(x < w/2, x > -w/2),np.logical_and(y < h/2, y > -h/2))
        rowColIdsWhereVisible = rowColCoordinates[whereInsideImage.tolist()[0],:]
        overlapMap[rowColIdsWhereVisible[:,0],rowColIdsWhereVisible[:,1]]+=1

        projectedDSM = imagePoints[0:2,whereInsideImage.tolist()[0]]
        sizeOfProjectedDSM = projectedDSM.shape[1]

        for i in range(0,sizeOfProjectedDSM):
            rowId = rowColIdsWhereVisible[i,0]
            colId = rowColIdsWhereVisible[i,1]
            if (rowId,colId) not in imageObservationsOfDSM.keys():
                imageObservationsOfDSM[(rowId,colId)] = geometry.ObservationsInImages()
            imageObservationsOfDSM[(rowId,colId)].add(imageCollectionId ,imageId, geometry.Point2D(projectedDSM[0,i],projectedDSM[1,i]))
    return (overlapMap, imageObservationsOfDSM)

def computeImageOverlapMultiprocess(*,rasterioDsm: rasterio.DatasetReader,
                    listOfImageCollections: list[geometry.ImageCollection],
                    numberOfProcesses: int) -> tuple[np.ndarray, dict[(int,int), geometry.ObservationsInImages] ]:

    model = rasterioDsm.read()
    if (len(model.shape) == 3):
        model = model[0,:,:]

    overlapMap = np.zeros(model.shape, dtype = int)


    coordinatesOfDSMPoints = rasterio_tools.raster2Array(rasterioDsm = rasterioDsm)

    whereNodata = np.where(coordinatesOfDSMPoints[2,:] == rasterioDsm.meta["nodata"])[0]
    coordinatesOfDSMPoints = np.delete(coordinatesOfDSMPoints, whereNodata, axis = 1)

    nRows = model.shape[0]
    nCols = model.shape[1]
    numberOfPoints = nRows*nCols
    xGrid, yGrid = np.meshgrid(range(0,nCols),range(0,nRows))
    rowColCoordinates = np.reshape(np.dstack((yGrid,xGrid)),(numberOfPoints,2))

    rowColCoordinates = np.delete(rowColCoordinates, whereNodata, axis = 0)

    listIfImagesForMultiprocessing = []
    
    for p in range(0,numberOfProcesses):
        listIfImagesForMultiprocessing.append([])
    #   listOfImgObservationsOfDSM.append({})

    counterOfImages = 0
    for imageCollection in listOfImageCollections:
        for imageId, image in imageCollection.images.items():
            listIfImagesForMultiprocessing[counterOfImages%numberOfProcesses].append(((imageCollection.id, imageId), image))
            counterOfImages += 1
     

    
    argsForMultiprocessing = [(processId, cp.copy(model.shape), cp.copy(coordinatesOfDSMPoints), cp.copy(rowColCoordinates),
                              cp.copy(listIfImagesForMultiprocessing[processId])) for processId in range(numberOfProcesses)]

    listOfImgObservationsOfDSM = []
    with multiprocessing.Pool(numberOfProcesses) as poolOfProcesses:
        for result in poolOfProcesses.starmap(projectDSMToImages, argsForMultiprocessing):
            print("obtained ", len(result[1]), " image data.")
            overlapMap = overlapMap + result[0]
            listOfImgObservationsOfDSM.append(result[1])



    for processId in range(1,numberOfProcesses):
        for rowCol, observationsForThisPoint in listOfImgObservationsOfDSM[processId].items():
             if rowCol not in listOfImgObservationsOfDSM[0].keys():
                 listOfImgObservationsOfDSM[0][rowCol] = geometry.ObservationsInImages()
             for obs in observationsForThisPoint.observations:
                listOfImgObservationsOfDSM[0][rowCol].observations.append(obs)   
            
    return overlapMap, listOfImgObservationsOfDSM[0]
            

def triangulatePoints(observationsForRasterCells: dict[tuple[int,int],geometry.ObservationsInImages], imageCollections : list[geometry.ImageCollection]):
    triangulatedObjectPoints = {}
    
    for rowCol, observations in observationsForRasterCells.items():
        numberOfObs = observations.getNumberOfPoints()
        if numberOfObs < 2:
            continue
        objectPoint = geometry.computeMultiVeiwIntersection(observations, imageCollections)
        triangulatedObjectPoints[rowCol] = objectPoint
    
    return triangulatedObjectPoints



def triangulatePointsMultiprocess(observationsForRasterCells: dict[tuple[int,int],geometry.ObservationsInImages],
                                 imageCollections : list[geometry.ImageCollection],
                                 numberOfProcesses: int )  -> dict[tuple[int,int], np.ndarray]:

    listOfResults = []

    listOfObservationChunks = []
    for processId in range(0, numberOfProcesses):
        listOfObservationChunks.append({})

    counterOfPoints = 0
    for rowCol, observations in observationsForRasterCells.items():
        listOfObservationChunks[counterOfPoints%numberOfProcesses][rowCol] = observations
        counterOfPoints += 1

    argsForMultiprocessing = [(listOfObservationChunks[processId].copy(), cp.copy(imageCollections) ) for processId in range(numberOfProcesses)]
    
    with multiprocessing.Pool(numberOfProcesses) as poolOfProcesses:
        for result in poolOfProcesses.starmap(triangulatePoints, argsForMultiprocessing):
            listOfResults.append(result)

    for processId in range(1,numberOfProcesses):
        for rowCol, point in listOfResults[processId].items():
            listOfResults[0][rowCol] = point

    return listOfResults[0]

def computeResidualRasters(referenceDsm: rasterio.DatasetReader, objectPointCoordinates: dict[tuple[int,int], np.ndarray]):
    referenceGrid = referenceDsm.read()
    if (len(referenceGrid.shape) == 3):
        referenceGrid = referenceGrid[0,:,:]
    
    rowCol2CoordsTransf = rasterio_tools.rasterioTransform2NumpyArray(referenceDsm.transform)
    
    for rowCol, evaluatedCoordinates in objectPointCoordinates.items():
        referenceCoordinates = np.matmul(rowCol2CoordsTransf, np.array([rowCol[0],rowCol[1],1]))
        print("ref_coords = ",referenceCoordinates," eval_coords = ", evaluatedCoordinates )