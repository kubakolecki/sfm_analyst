import rasterio
import rasterio.plot
import matplotlib.pyplot as plt

dataDierectory = "D:/DANE/tutorials/rasterio/dem_nederlands/"

DSM = rasterio.open(dataDierectory + "AHN2_05m_DSM.tif", driver="GTiff")
DTM = rasterio.open(dataDierectory + "AHN2_05m_DTM.tif", driver="GTiff")

print("DSM nodata is: ", DSM.nodata)
print("DTM nodata is: ", DTM.nodata)

print("printing metadata:")
print(DSM.meta)
print(DTM.meta)

plt.figure(1)
rasterio.plot.show(DSM, title='Digital Surface Model', cmap='gist_ncar')
plt.figure(2)
rasterio.plot.show(DTM, title='Digital Terrain Model', cmap='gist_ncar')
plt.show()

CHM = DSM.read() - DTM.read()
print(type(CHM))

kwargs = DSM.meta # Copy metadata of rasterio.io.DatasetReader
with rasterio.open(dataDierectory + "AHN2_05m_CHM.tif", 'w', **kwargs) as file:
    file.write(CHM.astype(rasterio.float32))