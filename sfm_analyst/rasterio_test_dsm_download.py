from owslib.wcs import WebCoverageService

webCoverageService = WebCoverageService('http://geodata.nationaalgeoregister.nl/ahn2/wcs?service=WCS', version='1.0.0')
print("contents of web coverage service:")
print(list(webCoverageService.contents))

print([op.name for op in webCoverageService.operations])

coverage = webCoverageService.contents['ahn2_05m_ruw']

print(coverage.boundingBoxWGS84)
print(coverage.supportedCRS)
print(coverage.supportedFormats)

x, y = 174100, 444100
bbox = (x-500, y-500, x+500, y+500)
response = webCoverageService.getCoverage(identifier='ahn2_05m_ruw', bbox=bbox, format='GEOTIFF_FLOAT32',
                           crs='urn:ogc:def:crs:EPSG::28992', resx=0.5, resy=0.5)
with open('D:/DANE/tutorials/rasterio/dem_nederlands/AHN2_05m_DSM.tif', 'wb') as file:
    file.write(response.read())

response = webCoverageService.getCoverage(identifier='ahn2_05m_int', bbox=bbox, format='GEOTIFF_FLOAT32',
                           crs='urn:ogc:def:crs:EPSG::28992', resx=0.5, resy=0.5)
with open('D:/DANE/tutorials/rasterio/dem_nederlands/AHN2_05m_DTM.tif', 'wb') as file:
    file.write(response.read())