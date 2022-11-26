"""
* **Write GJ to GPX converter**
* Run gpxcat -d 50 to merge NCR data
* **Write track splitter based on max points**
* Run existing gjwaypoints tool
* Run existing simplification process
"""

from math import asin, sin, cos, sqrt

def lldist((lat0, lon0), (lat1, lon1)):

    f1 = sin((lat0-lat1)/2)**2  
    f2 = cos(lat0) * cos(lat1)
    f3 = sin((lon1-lon1)/2)**2

    x = sqrt(f1 + f2 * f3)

    d = 2 * asin(x)
