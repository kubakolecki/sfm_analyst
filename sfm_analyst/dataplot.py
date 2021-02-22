import numpy as np
import matplotlib.pyplot as plt

D = np.loadtxt("D:\\DANE\\dydaktyka\\KarolinaPargielaDR\\residuals.txt", dtype= float)

print(D.shape)

plt.plot(D[:,1], D[:,0],".k")
plt.show()