import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches

import pyforefire as forefire
from forefire_helper import *

## Simulation Parameters ##
nb_steps = 5                    # The number of step the simulation will execute
step_size = 50                  # The duration (in seconds) between each step
windU = 0                       # The Horizontal wind
windV = 0                       # The Vertical wind
fuel_file_path = './fuels.ff'   # The path of fuel file
fuel_type = 103                 # The type of used fuel


# Initialize pyforefire module
ff = forefire.ForeFire()

# Set advanced simulation parameters

ff["fuelsTable"] = standardRothermelFuelTable()
ff.setDouble("spatialIncrement",0.2)
ff.setDouble("minimalPropagativeFrontDepth",20)
ff.setDouble("perimeterResolution",1)
ff.setInt("atmoNX", 100)
ff.setInt("atmoNY", 100)
ff.setDouble("initialFrontDepth",5)
ff.setDouble("relax",.1)
ff.setDouble("smoothing",100)
ff.setDouble("z0",0.)
ff.setDouble("windU", windU) # Horizontal
ff.setDouble("windV", windV) # Vertical
ff.setInt("defaultFuelType",1)
ff.setInt("bmapLayer",1)
ff.setInt("defaultHeatType",0)
ff.setDouble("nominalHeatFlux",100000)
ff.setDouble("burningDuration",100)
ff.setDouble("maxFrontDepth",50)
ff.setDouble("minSpeed",.035)

# data_resolution (in meters)
data_resolution = 1
# total size of sim
sim_shape = (1000, 1000)
# domain_width & domain_height
domain_height = sim_shape[0]
domain_width = sim_shape[1]

ff["SWx"] = 0.
ff["SWy"] = 0.
ff["Lx"] = domain_width
ff["Ly"] = domain_height

    
domain_string = f'FireDomain[sw=({ff["SWx"]},{ff["SWy"]},0);ne=({ff["SWx"] + ff["Lx"]},{ff["SWy"] + ff["Ly"]},0);t=0]'
print(domain_string)
ff.execute(domain_string)

# Add the required Forefire layers
ff.addLayer("data","altitude","z0")
ff.addLayer("data","windU","windU")
ff.addLayer("data","windV","windV")
ff.addLayer("BRatio","BRatio","BRatio")
ff.addLayer("flux","heatFluxBasic","defaultHeatType")
ff.addLayer("propagation","Rothermel","propagationModel")

# Init fuel_map and altitude_map with zeros
fuel_map = np.zeros((1, 1) + sim_shape)
fuel_map.fill(fuel_type)
altitude_map = np.zeros((1, 1) + sim_shape)

# Create a list to save simulation params
sim_params = np.zeros(sim_shape).tolist()

for i in range(sim_shape[0]):
    for j in range(sim_shape[1]):
        # Create a dictionnary with current parameters
        one_sim_param = dict(
            ignition = (i, j),
            fuel = fuel_type,
            slope = 0,
            pathes = [],
            pathes_time = [],
            speeds = [],
            width = [],
            height = []
        )
        # Assign these params to the matrix containing all parameters
        sim_params[i][j] = one_sim_param

# Add the fuel_map and altitude_map to the firefront layers
ff.addIndexLayer("table", "fuel", 0, 0, 0, domain_width, domain_height, 0, fuel_map)
ff.addScalarLayer("table", "altitude", 0, 0, 0, domain_width, domain_height, 0, altitude_map)

ff.execute("\tFireFront[id=2;domain=0;t=0]")
ff.execute("\t\tFireNode[domain=0;loc=(525,520,0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute("\t\tFireNode[domain=0;loc=(525,590,0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute("\t\tFireNode[domain=0;loc=(550,560,0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute("\t\tFireNode[domain=0;loc=(575,590,0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute("\t\tFireNode[domain=0;loc=(575,520,0);vel=(0,0,0);t=0;state=init;frontId=2]")

# Loop over number of timesteps, step by step_size
pathes = []
for i in range(1, nb_steps+1):
    try:
        # Advance timestep by step_size
        print("goTo[t=%f]" % (i*step_size))
        ff.execute("goTo[t=%f]" % (i*step_size))
        # Get pathes from previous execution
        newPathes = printToPathe(ff.execute("print[]"))
        pathes += newPathes
        # Iterate over pathes to store each of them
        for myPath in newPathes:
            px, py = myPath.vertices[0]
            # Get corresponding indices to the sim_params matrix
            I,J = get_sub_domain_indices_from_location(px, py, 0, 0, domain_width, domain_height)
            # Store pathes and time
            sim_params[I][J]['pathes'].append(myPath.vertices)
            sim_params[I][J]['pathes_time'].append(i*step_size)

    except KeyboardInterrupt:
        # Keyboard interrupt in case simulation take a while and we want to show current state of simulation
        break

ffplotExtents =(float(ff["SWx"]),float(ff["SWx"]) + float(ff["Lx"]),float(ff["SWy"]),float(ff["SWy"]) + float(ff["Ly"]))

plot_simulation(pathes,ff.getDoubleArray("fuel")[0,0,:,:] ,ff.getDoubleArray("altitude")[0,0,:,:],  ffplotExtents ,scalMap=ff.getDoubleArray("BMap")[0,0,:,:])

