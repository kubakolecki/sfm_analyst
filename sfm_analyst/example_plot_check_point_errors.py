import xtrelio

import numpy as np
import matplotlib.pyplot as plt

reportDirectory = "ExampleSimulateBaProblem/baReports"

N = 20
accuracy_start = 0.005
accuracy_step = 0.015

plotdata = np.zeros((N,2))


for reportId in range(0,N):
    reportFileName = reportDirectory + "/report_" + str(reportId) + ".txt"
    residuals = xtrelio.getCheckPointRMSEFromXtrelReport(reportFileName)
    plotdata[reportId,1] = residuals[3,0]
    plotdata[reportId,0] = accuracy_start + reportId*accuracy_step


plt.plot(plotdata[:,0], plotdata[:,1])
plt.grid()
plt.xlabel("std. dev. of ground control points [m]")
plt.ylabel("RMSE on check points [m]")
plt.show()
