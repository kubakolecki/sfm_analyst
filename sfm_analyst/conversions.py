import numpy as np


def perspectiveCenter2Translation(perspectiveCenter, R):
    translation = -np.matmul(R,perspectiveCenter)
    return translation

def normalizeVector(v):
    norm=np.linalg.norm(v, ord=2)
    if norm == 0:
        norm=np.finfo(v.dtype).eps
    return v/norm

def degrees2Radians(deg):
    return np.pi*deg / 180.0

def radians2Degrees(rad):
    return 180.0*rad / np.pi

def angles2rotationMatrix(angles,sequence):
    s0 = np.sin(angles[0])
    s1 = np.sin(angles[1])
    s2 = np.sin(angles[2])
    c0 = np.cos(angles[0])
    c1 = np.cos(angles[1])
    c2 = np.cos(angles[2])
    Rz = np.array([[c2, -s2, 0.0]      
                   ,[s2, c2, 0.0]
                   ,[0.0, 0.0, 1.0]]);

    Ry = np.array([[c1, 0.0, s1]      
                   ,[0.0, 1.0, 0.0]
                   ,[-s1, 0.0, c1]]);

    Rx = np.array([[1.0, 0.0, 0.0]      
                   ,[0.0, c0, -s0]
                   ,[0.0, s0, c0]]);

    if sequence == "x-y-z":
        R = np.matmul(np.matmul(Rx,Ry), Rz)

    return R


#def rotationMarix2Quaternion(R):
#	if (R[4] > -R[8]) and (R[0] > - R[4]) and (R[0] > -R[8]):
#	    q[0] = 0.5*pow(1.0 + R[0] + R[4] + R[8],0.5)
#	    q[1] = (R[7]-R[5])/(4*q[0])
#	    q[2] = (R[2]-R[6])/(4*q[0])
#	    q[3] = (R[3]-R[1])/(4*q[0])
#	else:
#		if (R[4] < -R[8]) and (R[0] > R[4]) and (R[0] > -R[8]):
#			q[1] = 0.5*pow(1.0 + R[0] - R[4] - R[8],0.5)
#			q[0] = (R[7] - R[5])/(4*q[1])
#			q[2] = (R[3] + R[1])/(4*q[1])
#			q[3] = (R[2] + R[6])/(4*q[1])		
#		else:
#			if (R[4] > R[8]) and (R[0] < R[4]) and (R[0] < - R[8]):
#				q[2] = 0.5*pow(1.0 - R[0] + R[4] - R[8],0.5)
#				q[0] = (R[2] - R[6])/(4*q[2])
#				q[1] = (R[3] + R[1])/(4*q[2])
#				q[3] = (R[7] + R[5])/(4*q[2])
#			else:
#				q[3] = 0.5*pow(1.0 - R[0] - R[4] + R[8],0.5)
#				q[0] = (R[3] - R[1])/(4*q[3])
#				q[1] = (R[2] + R[6])/(4*q[3])
#				q[2] = (R[7] + R[5])/(4*q[3])
#	return q
#
#
#def quaternion2RotationMatrix(q):
#   
#    qn = normalizeVector(q)
#    
#    R = np.zeros((3,3))
#  
#    R[0,0] = qn[0]*qn[0] + qn[1]*qn[1] - qn[2]*qn[2] - qn[3]*qn[3]
#    R[0,1] = 2*(qn[1]*qn[2] - qn[0]*qn[3])
#    R[0,2] = 2*(qn[1]*qn[3] + qn[0]*qn[2])
#    
#    R[1,0] = 2*(qn[1]*qn[2] + qn[0]*qn[3]);
#    R[1,1] = qn[0]*qn[0] - qn[1]*qn[1] + qn[2]*qn[2] - qn[3]*qn[3]
#    R[1,2] = 2*(qn[2]*qn[3] - qn[0]*qn[1])
#    
#    R[2,0] = 2*(qn[1]*qn[3] - qn[0]*qn[2])
#    R[2,1] = 2*(qn[2]*qn[3] + qn[0]*qn[1])
#    R[2,2] = qn[0]*qn[0] - qn[1]*qn[1] - qn[2]*qn[2] + qn[3]*qn[3]
#    
#    return R