import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
import pyforefire as forefire

from forefire_helper import *


## Simulation Parameters ##
nb_steps = 5                 # The number of step the simulation will execute
step_size =   3600              # The duration (in seconds) between each step
windU = 0                       # The Horizontal wind
windV = 3                      # The Vertical wind
fuel_file_path = './fuels.ff'   # The path of fuel file
fuel_type = 82
k = [.10,.30,.60]            # % of fuel
data_resolution = 50
sub_sim_shape = (80,60)
k_coeffs = [.45,.47,.49,.51]   

# Initialize pyforefire module
ff = forefire.ForeFire()

# Set advanced simulation parameters
ff.setString("ForeFireDataDirectory", ".")
ff.setString("fuelsTableFile", fuel_file_path)
ff.setDouble("spatialIncrement",0.4)
ff.setDouble("minimalPropagativeFrontDepth",20)
ff.setDouble("perimeterResolution",4)
ff.setDouble("initialFrontDepth",5)
ff.setDouble("relax",.2)
ff.setDouble("smoothing",0)
ff.setDouble("z0",0.)
ff.setDouble("windU", windU) # Horizontal
ff.setDouble("windV", windV) # Vertical
ff.setInt("defaultFuelType",1)
ff.setInt("bmapLayer",1)
ff.setInt("defaultHeatType",0)
ff.setDouble("nominalHeatFlux",100000)
ff.setDouble("burningDuration",100)
ff.setDouble("maxFrontDepth",50)
ff.setDouble("minSpeed",0.005)

sim_shape = (sub_sim_shape[0], sub_sim_shape[1]*len(k_coeffs))
domain_height = sim_shape[0] * data_resolution
domain_width = sim_shape[1] * data_resolution

# setting the velues for the fluxed models diagnostics
ff.setInt("atmoNX", sim_shape[1] )
ff.setInt("atmoNY", sim_shape[0] )


print("Domain shape ",sim_shape, data_resolution) 
fuel_map = np.zeros((1, 1) + sim_shape)

print("fuelmap shape", fuel_map.shape)
altitude_map = np.zeros((1, 1) + sim_shape)

for i, k in enumerate(k_coeffs):
    fuel_map[0, 0, :, sub_sim_shape[1] *i:sub_sim_shape[1] * (i + 1)] = fill_random((sub_sim_shape[0], sub_sim_shape[1]), k, fuel_type)

ff["SWx"] = 0.
ff["SWy"] = 0.
ff["Lx"] = domain_width
ff["Ly"] = domain_height

    
domain_string = f'FireDomain[sw=({ff["SWx"]},{ff["SWy"]},0);ne=({ff["SWx"] + ff["Lx"]},{ff["SWy"] + ff["Ly"]},0);t=0]'
print(domain_string)
ff.execute(domain_string)
ff.execute("FireDomain[sw=(0.,0.,0.);ne=(%i,%i,0.);t=0.]" % (domain_width, domain_height))

# Add the required Forefire layers
ff.addLayer("data","altitude","z0")
ff.addLayer("data","windU","windU")
ff.addLayer("data","windV","windV")
ff.addLayer("BRatio","BRatio","BRatio")
ff.addLayer("flux","heatFluxBasic","defaultHeatType")
ff.addLayer("propagation","Rothermel","propagationModel")


ff.addIndexLayer("table", "fuel",           0,          0, 0, domain_width, domain_height, 0, fuel_map)
ff.addScalarLayer("table", "altitude", 0, 0, 0, domain_width, domain_height, 0, altitude_map)


# Start ignitions with previoulsy computed ignitions points
for i in range(len(k_coeffs)):
    ignition_string = "startFire[loc=(%i,%i,0.);vel=(1.,1.,0.);t=0.]" % ( data_resolution * (0.5+i) * sub_sim_shape[1] , 5*data_resolution)
    print(ignition_string)
    ff.execute(ignition_string)
    

# Loop over number of timesteps, step by step_size
pathes = []
for i in range(1, nb_steps+1):
    try:
        print("goTo[t=%f]" % (i*step_size))
        ff.execute("goTo[t=%f]" % (i*step_size))
        pathes  += printToPathe(ff.execute("print[]"))

    except KeyboardInterrupt:
        break

ffplotExtents =(float(ff["SWx"]),float(ff["SWx"]) + float(ff["Lx"]),float(ff["SWy"]),float(ff["SWy"]) + float(ff["Ly"]))

plot_simulation(pathes,ff.getDoubleArray("fuel")[0,0,:,:] ,None,  ffplotExtents ,scalMap=ff.getDoubleArray("BMap")[0,0,:,:])
