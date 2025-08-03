import numpy as np
import math

def min_max_scaling(arr, range = (0, 255)):
   min, max = range
   x = min + ( (arr - np.min(arr)) * (max - min) / (np.max(arr) - np.min(arr)) )
   return x