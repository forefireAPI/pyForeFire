import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import math
import xarray as xr
import pyforefire as forefire
from datetime import datetime
import time

from forefire_helper import *

landscape_file_path = "sampleUVCoeffLandscape.nc"

ff = forefire.ForeFire()
 
ff["fuelsTable"] = standardRothermelFuelTable()
ff["propagationModel"] = "Rothermel"
ff["spatialIncrement"] = 3
ff["perimeterResolution"] = 10
ff["minimalPropagativeFrontDepth"] = 20
ff["relax"] = 0.5
ff["minSpeed"] = 0.30
ff["propagationSpeedAdjustmentFactor"] = 1
ff["bmapLayer"] = 1

testRunMode = "Instructions"

if testRunMode == "Script":
    ff.execute(f'loadData[{landscape_file_path};2009-07-24T11:37:39Z]')
    domain_string = f'FireDomain[sw=({ff["SWx"]},{ff["SWy"]},0);ne=({ff["SWx"] + ff["Lx"]},{ff["SWy"] + ff["Ly"]},0);t=0]'


if testRunMode == "Instructions":
    
    lcp = xr.open_dataset(landscape_file_path)
    dom = lcp.domain.attrs    
    
    fuel_map = lcp.fuel.data
    altitude_map = lcp.altitude.data
    wind_map = lcp.wind.data
    windU=wind_map[0:1,:,:,:]
    windV=wind_map[1:2,:,:,:]
    
    ff["SWx"] = float(dom["SWx"])
    ff["SWy"] = float(dom["SWy"])
    ff["Lx"] = float(dom["Lx"])
    ff["Ly"] = float(dom["Ly"])
  
    ff.setString("ISOdate", "2009-07-24T11:37:39Z")

    date_obj = datetime.strptime(ff.getString("ISOdate"), "%Y-%m-%dT%H:%M:%SZ")
    secs = date_obj.hour * 3600 + date_obj.minute * 60 + date_obj.second
    year = date_obj.year
    start_of_year = datetime(year, 1, 1)
    yday = (date_obj - start_of_year).days + 1
    
    ff.setInt("refYear", year)
    ff.setInt("refDay", yday)
    ff.setInt("refTime", secs)
    
    domain_string = f'FireDomain[sw=({dom["SWx"]},{dom["SWy"]},0);ne=({dom["SWx"] + dom["Lx"]},{dom["SWy"] + dom["Ly"]},0);t=0]'
    ff.execute(domain_string)
    
    
    ff.addLayer("propagation",ff["propagationModel"],"propagationModel")
    ff.addIndexLayer("table", "fuel", dom["SWx"], dom["SWy"], 0, dom["Lx"], dom["Ly"], 0, fuel_map)
    ff.addScalarLayer("data", "altitude", dom["SWx"], dom["SWy"], 0, dom["Lx"], dom["Ly"], 0, altitude_map)
        
    ff.addScalarLayer("windScalDir", "windU", dom["SWx"], dom["SWy"], 0, dom["Lx"], dom["Ly"], 0, windU)
    ff.addScalarLayer("windScalDir", "windV", dom["SWx"], dom["SWy"], 0, dom["Lx"], dom["Ly"], 0, windV)


ff.execute("startFire[loc=(506666,4625385,0);t=0]")
ff.execute("startFire[loc=(506666,4614485,0);t=0]")
ff.execute("startFire[loc=(480666,4615385,0);t=0]")
start_time = time.time()

pathes = []

nb_steps = 10  # The number of steps the simulation will execute
step_size = 300  # The duration (in seconds) between each step
angle_deg = 30.0  # The angle by which to rotate the vector at each step
norm = 20  # The norm of the vector

for i in range(nb_steps):
    rotation_angle_rad = math.radians(i * angle_deg)
    herex = norm * math.cos(rotation_angle_rad)
    herey = norm * math.sin(rotation_angle_rad)
    angle_deg = angle_deg-(0.5)
    try:
        new_out = ff.execute("print[]")
        newPathes = printToPathe(new_out)
        ff.execute(f"trigger[wind;loc=(0.,0.,0.);vel=({herex},{herey},0);t=0.]")
        ff.execute("step[dt=%f]" % (step_size))
        pathes += newPathes
        print("Iteration ",i,"/",nb_steps, " angle ", angle_deg)
        
    except KeyboardInterrupt:
        break

end_time = time.time()

# Calculate the total duration
duration = end_time - start_time

# Finally, plot simulations and show stats
ffplotExtents =(float(ff["SWx"]),float(ff["SWx"]) + float(ff["Lx"]),float(ff["SWy"]),float(ff["SWy"]) + float(ff["Ly"]))
 
print(f"Total time taken: {duration} seconds")
plot_simulation(pathes,ff.getDoubleArray("fuel")[0,0,:,:] ,ff.getDoubleArray("altitude")[0,0,:,:],  ffplotExtents ,scalMap=ff.getDoubleArray("BMap")[0,0,:,:])
