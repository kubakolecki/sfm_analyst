import rasterio
import numpy as np

def rasterioTransform2NumpyArray(rasterioTransform):
    affineTransformationMatrix = np.array([[rasterioTransform[0],rasterioTransform[1],rasterioTransform[2]],
                                           [rasterioTransform[3],rasterioTransform[4],rasterioTransform[5]],
                                           [rasterioTransform[6],rasterioTransform[7],rasterioTransform[8]]])
    return affineTransformationMatrix

def raster2Array(*,rasterioDsm: rasterio.DatasetReader) ->np.ndarray:
    model = rasterioDsm.read()
    if (len(model.shape) == 3):
        model = model[0,:,:]
    nRows = model.shape[0]
    nCols = model.shape[1]
    numberOfPoints = nRows * nCols

    pixelToWorldTransf  = rasterioTransform2NumpyArray(rasterioDsm.transform)

    xGrid, yGrid = np.meshgrid(range(0,nCols),range(0,nRows))
    listOfRowColCoords = np.reshape(np.dstack((yGrid,xGrid,np.ones((nRows,nCols)))),(numberOfPoints,3))

    dsmCoordinates = np.matmul(pixelToWorldTransf,np.transpose(listOfRowColCoords))
    dsmCoordinates[2,:] = np.reshape(model,(numberOfPoints))
    dsmCoordinates = np.vstack((dsmCoordinates, np.ones(numberOfPoints) ))

    return dsmCoordinates
                       