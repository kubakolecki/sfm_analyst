import xtrelio as xtrelio
import sfmio as sfmio

xtrelReportFile = "California/report.txt"
imagesWithEstimatedEO = xtrelio.createImageCollectionFromXtrelReport(xtrelReportFile, 0)
objectPointCollection = xtrelio.createObjectPointCollectionFromXtrelReport(xtrelReportFile, 0, 0)

sfmio.writeImageCollectionToObj(imagesWithEstimatedEO, "california_estimated" ,imageWidthInMeters = 12.0, axesLenghtInMeters = 9.0)
sfmio.writeObjectPointsToFile("object_points_estimated.txt", objectPointCollection)

listOfImageCollections = []
listOfObjectPointCollections = []

listOfImageCollections.append(imagesWithEstimatedEO)
listOfObjectPointCollections.append(objectPointCollection)

sfmio.writeRaysToDxf("rays_estimated_tie.dxf", listOfObjectPointCollections, listOfImageCollections, "tie", 9)
sfmio.writeRaysToDxf("rays_estimated_controll.dxf", listOfObjectPointCollections, listOfImageCollections, "controll", 1)