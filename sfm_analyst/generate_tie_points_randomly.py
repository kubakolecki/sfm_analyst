import numpy as np

pathFileOutput = r"D:\DANE\Visual_Studio\Python\sfm_analyst\sfm_analyst\ExampleSimulateBaProblem\inputData\bridge_tie_points.txt"

numberOfPoints = 240
idOfFirstPoint = 1000
randomNumberGenerator =  np.random.default_rng()

#generating pints in vertical plane layout
rangeX = (0.0,13.0)
rangeY = (-0.2, 0.2)
rangeZ = (2.0, 12.0)
normalVector = [0,-1,0]
visibilityDistance = 10.0

x = randomNumberGenerator.uniform(rangeX[0], rangeX[1], numberOfPoints)
y = randomNumberGenerator.uniform(rangeY[0], rangeY[1], numberOfPoints)
z = randomNumberGenerator.uniform(rangeZ[0], rangeZ[1], numberOfPoints)

outputFile = open(pathFileOutput,'w')

for (id,x,y,z) in zip(range(idOfFirstPoint,idOfFirstPoint+numberOfPoints),x, y, z):
    outputFile.write("%d,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%2f\n" % (id, x, y, z, normalVector[0], normalVector[1], normalVector[2],visibilityDistance))


#generating pints in horizontal plane layout

rangeX = (0.0,13.0)
rangeY = (0.0, 8.0)
rangeZ = (11.9, 12.1)
normalVector = [0,0,1]
visibilityDistance = 10.0

x = randomNumberGenerator.uniform(rangeX[0], rangeX[1], numberOfPoints)
y = randomNumberGenerator.uniform(rangeY[0], rangeY[1], numberOfPoints)
z = randomNumberGenerator.uniform(rangeZ[0], rangeZ[1], numberOfPoints)

idOfFirstPoint = 5000

for (id,x,y,z) in zip(range(idOfFirstPoint,idOfFirstPoint+numberOfPoints),x, y, z):
    outputFile.write("%d,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%2f\n" % (id, x, y, z, normalVector[0], normalVector[1], normalVector[2],visibilityDistance))


outputFile.close()