from scipy.stats import norm
from scipy.stats import shapiro
my_data = norm.rvs(size=500) #tutaj musisz podstawic Twoje dane <3
resultShapiroWilk = shapiro(my_data)
print(resultShapiroWilk)
