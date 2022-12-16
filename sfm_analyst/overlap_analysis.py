from asyncio import proactor_events
import numpy as np
import geometry
import rasterio
import multiprocessing
import rasterio_tools
import copy as cp


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

def projectDSMToImages(processId: int, coordinatesOfDSMPoints, rowColCoordinates, listOfImageData, overlapMap, imageObservationsOfDSM, lock: multiprocessing.Lock):
    for imageData in listOfImageData:
        imageCollectionId = imageData[0][0]
        imageId = imageData[0][1]
        image = imageData[1]

        print(f"process {processId}, projecting to image {imageId} in collection {imageCollectionId}")
            
        imagePoints = geometry.project(image,coordinatesOfDSMPoints)
        x = imagePoints[0,:]
        y = imagePoints[1,:]
        w = image.camera.width
        h = image.camera.height
        whereInsideImage = np.logical_and(np.logical_and(x < w/2, x > -w/2),np.logical_and(y < h/2, y > -h/2))
        rowColIdsWhereVisible = rowColCoordinates[whereInsideImage.tolist()[0],:]
        with lock:
            overlapMap[rowColIdsWhereVisible[:,0],rowColIdsWhereVisible[:,1]]+=1

        projectedDSM = imagePoints[0:2,whereInsideImage.tolist()[0]]
        sizeOfProjectedDSM = projectedDSM.shape[1]

        for i in range(0,sizeOfProjectedDSM):
            rowId = rowColIdsWhereVisible[i,0]
            colId = rowColIdsWhereVisible[i,1]
            if (rowId,colId) not in imageObservationsOfDSM.keys():
                imageObservationsOfDSM[(rowId,colId)] = geometry.ObservationsInImages()
            imageObservationsOfDSM[(rowId,colId)].add(imageCollectionId ,imageData[0], geometry.Point2D(projectedDSM[0,i],projectedDSM[1,i]))

def projectDSMToImagesB(processId: int, shapeOfRaster, coordinatesOfDSMPoints, rowColCoordinates, listOfImageData):
    
    overlapMap = np.zeros(shapeOfRaster, dtype = int)
    imageObservationsOfDSM = {}

    for imageData in listOfImageData:
        imageCollectionId = imageData[0][0]
        imageId = imageData[0][1]
        image = imageData[1]

        #print(f"in projectDSMToImagesB process {processId}, projecting to image {imageId} in collection {imageCollectionId}")
            
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
    
    for p in range(0,numberOfProcesses):
        print("thread ",p )
        for imageData in listIfImagesForMultiprocessing[p]:
            print(imageData[0])

    
    #lock = multiprocessing.Lock()

    
    argsForMultiprocessing = [(processId, cp.copy(model.shape), cp.copy(coordinatesOfDSMPoints), cp.copy(rowColCoordinates),
                              cp.copy(listIfImagesForMultiprocessing[processId])) for processId in range(numberOfProcesses)]

    #poolOfProcesses = multiprocessing.Pool(numberOfProcesses)
    listOfImgObservationsOfDSM = []
    with multiprocessing.Pool(numberOfProcesses) as poolOfProcesses:
        for result in poolOfProcesses.starmap(projectDSMToImagesB, argsForMultiprocessing):
            print("obtained ", len(result[1]), " image data.")
            overlapMap = overlapMap + result[0]
            listOfImgObservationsOfDSM.append(result[1])

    #processes = [multiprocessing.Process(target=projectDSMToImages,
    #                                    args=(processId, coordinatesOfDSMPoints, rowColCoordinates, listIfImagesForMultiprocessing[processId],
    #                                          overlapMap, listOfImgObservationsOfDSM[processId], lock )  ) for processId in range(numberOfProcesses)]
    #
    #for process in processes:
    #    process.start()
    #
    #for process in processes:
    #    process.join()
    #
    #for p in range(0,numberOfProcesses):
    #    print(f"list id {p}: number of points: {len(listOfImgObservationsOfDSM[p])}")

    for processId in range(1,numberOfProcesses):
        for rowCol, observationsForThisPoint in listOfImgObservationsOfDSM[processId].items():
             if rowCol not in listOfImgObservationsOfDSM[0].keys():
                 listOfImgObservationsOfDSM[0][rowCol] = geometry.ObservationsInImages()
             for obs in observationsForThisPoint.observations:
                listOfImgObservationsOfDSM[0][rowCol].observations.append(obs)   
            
    return overlapMap, listOfImgObservationsOfDSM[0]
            


