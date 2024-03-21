import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches

import pyforefire as forefire


## Simulation Parameters ##
nb_steps = 5                    # The number of step the simulation will execute
step_size = 50                  # The duration (in seconds) between each step
windU = 0                       # The Horizontal wind
windV = 0                       # The Vertical wind
fuel_file_path = './fuels.ff'   # The path of fuel file
fuel_type = 103                 # The type of used fuel

# Functions definitions
def get_sub_domain_indices_from_location(x, y, originX, originY, domain_width, domain_height):
    """
    Used for retrieve indices of coordinates inside simulation matrix
    """
    i = np.floor(((x - originX) / domain_width))
    j = np.floor(((y - originY) / domain_height))
    return int(i), int(j)

def maxDiff(a):
    """
    Used for get the maximum difference along first axis of an array
    """
    vmin = a[0]
    dmax = 0
    for i in range(len(a)):
        if (a[i] < vmin):
            vmin = a[i]
        elif (a[i] - vmin > dmax):
            dmax = a[i] - vmin
    return dmax

def getLocationFromLine(line):
    """
    Return the location of current node (line).
    """
    llv = line.split("loc=(")
    if len(llv) < 2: 
        return None
    llr = llv[1].split(",")
    if len(llr) < 3: 
        return None
    return (float(llr[0]),float(llr[1]))

def printToPathe(linePrinted):
    """
    Compute the current results of simulation to pathes.
    """
    fronts = linePrinted.split("FireFront")
    pathes = []
    for front in fronts[1:]:
        nodes = front.split("FireNode")[1:]
        if len(nodes) > 0:
            Path = mpath.Path
            codes = []
            verts = []
            firstNode = getLocationFromLine(nodes[0])
            codes.append(Path.MOVETO)
            verts.append(firstNode)

            for node in nodes[:]:
                newNode = getLocationFromLine(node)
                codes.append(Path.LINETO)
                verts.append(newNode)
            codes.append(Path.LINETO)
            verts.append(firstNode)
            pathes.append(mpath.Path(verts, codes))

    return pathes

def plot_simulation(ff, pathes, fuel_map, altitude_map, domain_width, domain_height, sim_shape):
    """
    Used for plot 4 axis graph, with Heatflux, Fuels, Altitude plotted under simulation, 
    and Statistics for the last axis.
    """
    # Create a figure with 4 axis (4 subplots)
    fig, ax = plt.subplots(figsize=(10,7), dpi=120)

    # Plot current firefronts to the first 3 subplots
    for path in pathes:
        patch = mpatches.PathPatch(path, edgecolor='red', facecolor='none', alpha=1)
        ax.add_patch(patch)
        ax.grid()
        ax.axis('equal')

    plt.show()


# Initialize pyforefire module
ff = forefire.ForeFire()

# Set advanced simulation parameters
ff.setString("ForeFireDataDirectory", ".")
ff.setString("fuelsTableFile", fuel_file_path)
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
domain_width = sim_shape[0]
domain_height = sim_shape[1]

# Create a FireDomain
# NOTE: FireDomain use meters as values
ff.execute("FireDomain[sw=(0.,0.,0.);ne=(%i,%i,0.);t=0.]" % (domain_width, domain_height))

# Add the required Forefire layers
ff.addLayer("data","altitude","z0")
ff.addLayer("data","windU","windU")
ff.addLayer("data","windV","windV")
ff.addLayer("BRatio","BRatio","BRatio")
ff.addLayer("flux","heatFluxBasic","defaultHeatType")
ff.addLayer("propagation","Rothermel","propagationModel")

# Init fuel_map and altitude_map with zeros
fuel_map = np.zeros(sim_shape)
fuel_map.fill(fuel_type)
altitude_map = np.zeros(sim_shape)

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


# Finally, plot simulations and show stats
plot_simulation(ff, pathes, fuel_map, altitude_map, domain_width, domain_height, sim_shape)
