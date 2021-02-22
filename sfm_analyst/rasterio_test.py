import numpy as np
import rasterio
import rasterio.plot

directory = "D:/DANE/tutorials/rasterio/landsat_data/"

greenband = rasterio.open(directory + "LC81980242014260LGN00_sr_band4.tif")
print("green band opened")
print(greenband.nodata)
print(greenband.bounds)

print(greenband.transform)
mirband = rasterio.open(directory + "LC81980242014260LGN00_sr_band6.tif")
print("mir band opened")

green = greenband.read(1).astype(float)
print("green band read")
print(green.shape)
print(green[100,200])

mir = mirband.read(1).astype(float)
print("mir band read")
print(mir.shape)


np.seterr(divide='ignore', invalid='ignore')  # Allow division by zero
mndwi = np.empty(greenband.shape, dtype=rasterio.float32)  # Create empty matrix
check = np.logical_or(mir > 0.0, green > 0.0)  # Create check raster with True/False values
mndwi = np.where(check, (green - mir) / (green + mir), -999)  # Calculate MNDWI

water = np.where(mndwi > 0, 1, 0) # Set values above 0 as water and otherwise leave it at 0

rasterio.plot.show(green, cmap = 'Greys' )
plt.show()