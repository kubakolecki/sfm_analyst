import xtrelio
import os as os
import numpy as np
import matplotlib.pyplot as plt


raportDirectory = r"D:\DANE\Visual_Studio\Python\sfm_analyst\sfm_analyst\ExampleSimulateBaProblem\archiveReports\baReports_num_of_gcp"
reportFiles = [f for f in os.listdir(raportDirectory) if os.path.isfile(os.path.join(raportDirectory, f))]

print("number of report files: ", len(reportFiles))

errorsForPlotting = np.zeros((len(reportFiles), 4))
sigmaZeroForPlotting = np.zeros((len(reportFiles), 2))

indicesOfLargeSigma = []

counter = 0
for reportFile in reportFiles:
    reportFileFullPath = os.path.join(raportDirectory, reportFile )
    pointStatistics = xtrelio.getNumberOfPointsFromXtrelReport(reportFileFullPath)
    gcpErrors = xtrelio.getCheckPointRMSEFromXtrelReport(reportFileFullPath)
    sigma = xtrelio.getSigmaZeroFromXtrelReport(reportFileFullPath)
    if (sigma > 2): #a sort of herustic check if optimization was scucessfull
        indicesOfLargeSigma.append(counter)
    sigmaZeroForPlotting[counter,0] = pointStatistics["control"]
    sigmaZeroForPlotting[counter,1] = sigma
    errorsForPlotting[counter,0] = pointStatistics["control"]
    errorsForPlotting[counter,1] = np.sqrt( gcpErrors[0]*gcpErrors[0] + gcpErrors[1]*gcpErrors[1]) #horizontal (2D, XY) error
    errorsForPlotting[counter,2] = gcpErrors[2] #Z error
    errorsForPlotting[counter,3] = gcpErrors[3] #3D error (XYZ)
    counter = counter + 1

errorsForPlottingSelected = np.delete(errorsForPlotting, obj = indicesOfLargeSigma, axis = 0)
   
plt.figure(1)
plt.plot(errorsForPlottingSelected[:,0], errorsForPlottingSelected[:,1],"ok")
plt.title("horizontal (2D, XY) error")
plt.xlabel("number of control points")
plt.ylabel("check point XY RMSE [m]")

plt.figure(2)
plt.plot(errorsForPlottingSelected[:,0], errorsForPlottingSelected[:,2],"ok")
plt.title("vertical (Z) error")
plt.xlabel("number of control points")
plt.ylabel("check point Z RMSE [m]")

plt.figure(3)
plt.plot(errorsForPlottingSelected[:,0], errorsForPlottingSelected[:,2],"ok")
plt.title("absolute (3D XYZ) error")
plt.xlabel("number of control points")
plt.ylabel("check point XYZ RMSE [m]")

plt.figure(4)
plt.plot(sigmaZeroForPlotting[:,0], sigmaZeroForPlotting[:,1],"ok" )
plt.xlabel("number of control points")
plt.ylabel("sigma zero [-]")


plt.show()




