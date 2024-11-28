import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches

import pyforefire as forefire
from forefire_helper import *
import time

## Simulation Parameters ##
nb_steps = 10                # The number of step the simulation will execute
step_size = 200             # The duration (in seconds) between each step
windU = 0                       # The Horizontal wind
windV = 0                       # The Vertical wind
 
fuel_type = 1                 # The type of used fuel


# Initialize pyforefire module
ff = forefire.ForeFire()

def testAnnFuelTable():
    return """Index;Rhod;sd;Ta
                0;0;0.68;0.097
                1;1;0.73;0.44
                2;2;0.36;0.050
                3;3;0.11;0.05
                4;4;0.92;0.22"""

# Set advanced simulation parameters

ff["fuelsTable"] = testAnnFuelTable()
ff["FFANNPropagationModelPath"] = "/Users/filippi_j/soft/pyForeFire/test/mbase.ffann"
ff["spatialIncrement"] = 0.5
ff["minimalPropagativeFrontDepth"] = 2
ff["perimeterResolution"] = 5
ff["relax"] = 0.5
ff["windU"] = windU  # Horizontal
ff["windV"] = windV  # Vertical
ff["defaultFuelType"] = 1
ff["bmapLayer"] = 1
ff["minSpeed"] = 0.035

 
ff.execute("setParameter[debugFronts=1]")
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
#print(domain_string)
ff.execute(domain_string)

# Add the required Forefire layers
#ff.addLayer("data","altitude","z0")
ff.addLayer("data","windU","windU")
ff.addLayer("data","windV","windV")
ff.addLayer("BRatio","BRatio","BRatio")
#ff.addLayer("flux","heatFluxBasic","defaultHeatType")
ff.addLayer("propagation","ANNPropagationModel","propagationModel")

ff["bmapLayer"] = 1
# Init fuel_map and altitude_map with zeros

fuel_map = np.random.randint(0, 5, size=(1, 1) + sim_shape) 
half_x, half_y = sim_shape[0] // 2, sim_shape[1] // 2
 
fuel_map[0, 0, :half_x, :half_y] = 0 
fuel_map[0, 0, :half_x, half_y:] = 1 
fuel_map[0, 0, half_x:, :half_y] = 2
 
fuel_map[0, 0, half_x:, half_y:] = 3 
 

# Create a grid of x and y values
x = np.linspace(0, 8 * np.pi, sim_shape[0])
y = np.linspace(0, 12 * np.pi, sim_shape[1])
x, y = np.meshgrid(x, y)

# Generate the 2D sine function
altitude_map = np.sin(x) * np.sin(y)

# Scale the altitude values to range from 0 to 100
altitude_map = 100 * (altitude_map - altitude_map.min()) / (altitude_map.max() - altitude_map.min())

# Expand dimensions to match the original shape (1, 1, sim_shape[0], sim_shape[1])
altitude_map = altitude_map[np.newaxis, np.newaxis, :, :]

# Add the fuel_map and altitude_map to the firefront layers
ff.addIndexLayer("table", "fuel", 0, 0, 0, domain_width, domain_height, 0, fuel_map)
ff.addScalarLayer("table", "altitude", 0, 0, 0, domain_width, domain_height, 0, altitude_map)

ff.execute("\tFireFront[id=2;domain=0;t=0]")
ff.execute("\t\tFireNode[domain=0;loc=(300,300,0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute("\t\tFireNode[domain=0;loc=(300,700,0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute("\t\tFireNode[domain=0;loc=(600,700,0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute("\t\tFireNode[domain=0;loc=(600,650,0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute("\t\tFireNode[domain=0;loc=(350,650,0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute("\t\tFireNode[domain=0;loc=(350,350,0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute("\t\tFireNode[domain=0;loc=(650,350,0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute("\t\tFireNode[domain=0;loc=(650,700,0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute("\t\tFireNode[domain=0;loc=(700,700,0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute("\t\tFireNode[domain=0;loc=(700,300,0);vel=(0,0,0);t=0;state=init;frontId=2]")

# Loop over number of timesteps, step by step_size
pathes = []

start_time = time.time()
for i in range(1, nb_steps+1):
    try:
        # Advance timestep by step_size
   #     print("goTo[t=%f]" % (i*step_size))
        ff.execute("goTo[t=%f]" % (i*step_size))
        # Get pathes from previous execution
        newPathes = printToPathe(ff.execute("print[]"))
        pathes += newPathes
    except KeyboardInterrupt:
        # Keyboard interrupt in case simulation take a while and we want to show current state of simulation
        break

end_time = time.time()
duration = end_time - start_time
print(f"Total time taken: {duration} seconds")



ffplotExtents =(float(ff["SWx"]),float(ff["SWx"]) + float(ff["Lx"]),float(ff["SWy"]),float(ff["SWy"]) + float(ff["Ly"]))

plot_simulation(pathes,None,None,  ffplotExtents ,scalMap=ff.getDoubleArray("fuel")[0,0,:,:])
ff.execute("save[parameter=speed;filename=intensity.png;cmap=hot;histogram=True]")
#ff.execute("quit[]")


