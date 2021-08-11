import xtrelio

import numpy as np
import matplotlib.pyplot as plt

reportDirectory = "ExampleSimulateBaProblem/baReports"

N = 20
NSamples = 10
accuracy_start = 0.005
accuracy_step = 0.015

plotdata = np.zeros((N,2))


for reportId in range(0,N):
    for sample in range(0,NSamples):
        reportFileName = reportDirectory + "/report_" + str(reportId) + "_" + str(sample)  + ".txt"
        residuals = xtrelio.getCheckPointRMSEFromXtrelReport(reportFileName)
        plotdata[reportId,1] += residuals[3,0]
    plotdata[reportId,1] /= NSamples
    plotdata[reportId,0] = accuracy_start + reportId*accuracy_step


plt.plot(plotdata[:,0], plotdata[:,1])
plt.grid()
plt.xlabel("std. dev. of ground controll points [m]")
plt.ylabel("RMSE on check points [m]")
plt.show()
