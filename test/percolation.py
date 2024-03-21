import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches

import pyforefire as forefire


## Simulation Parameters ##
nb_steps = 10                   # The number of step the simulation will execute
step_size = 300                 # The duration (in seconds) between each step
windU = 0                       # The Horizontal wind
windV = 4                       # The Vertical wind
fuel_file_path = './fuels.ff'   # The path of fuel file
fuel_type = 82
k = [.1, .52, .55, .55]            # % of fuel
start_end_zone_pct = 1/8        # % size of start & end zones


# Functions definitions
def get_sub_domain_indices_from_location(x, y, originX, originY, domain_width, domain_height, shape_multisim):
    """
    Used for retrieve indices of coordinates inside simulation matrix
    """
    i = np.floor(((x - originX) / domain_width) * shape_multisim[0])
    j = np.floor(((y - originY) / domain_height) * shape_multisim[1])
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

def genAltitudeMap(slope_coef, sub_sim_shape, data_resolution):
    """
    Generate a matrix of altitudes given a slope coefficient
    """
    slope = np.linspace(0, 1, sub_sim_shape[1])
    slope = np.repeat(slope, sub_sim_shape[0])
    slope = slope.reshape(sub_sim_shape[1], sub_sim_shape[0]).T
    return slope * slope_coef * (data_resolution / 5)


def map_fuel_to_colors(fuelmap, fuel_list):
    """
    Convert a fuel_map for use with colors.
    The returned fuel_map values are replaced by indices of fuels from fuel_list.
    """
    for i in range(len(fuelmap)):
        for j in range(len(fuelmap[0])):
            try:
                fuelmap[i][j] = fuel_list.index(fuelmap[i][j]) + 1
            except ValueError:
                fuelmap[i][j] = 0
    return fuelmap


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


def plot_simulation(pathes, fuel_map, domain_width, domain_height):
    """
    Used for plot 4 axis graph, with Heatflux, Fuels, Altitude plotted under simulation, 
    and Statistics for the last axis.
    """
    # Create a figure with 2 axis (2 subplots)
    fig, ax = plt.subplots(figsize=(10,7), dpi=120)

    # Get fuel_map matrix
    fuels = np.transpose(fuel_map.reshape(fuel_map.shape[0], fuel_map.shape[1], 1))[0]
    fuels = map_fuel_to_colors(fuels, [0, 82]) # Convert fuels indices to colors

    # Plot Fuels
    CS = ax.imshow(fuels, cmap=plt.cm.grey, interpolation='nearest', origin='lower', extent=(0,domain_width,0,domain_height))
    plt.colorbar(CS)

    # bounds = [0, 1]
    # cmap = mpl.colors.ListedColormap(['brown', 'green'])
    # norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
    # CS = ax.imshow(fuels, cmap=cmap, interpolation='nearest', origin='lower', extent=(0,domain_width,0,domain_height))
    # # plt.colorbar(plt.cm.ScalarMappable(cmap=cmap, norm=norm), cax=ax)
    # plt.colorbar(CS, norm=norm)

    path_colors = ['brown', 'red', 'orange']

    # Plot current firefronts to the first 3 subplots
    for p, paths in enumerate(pathes):
        for path in paths:
            patch = mpatches.PathPatch(path, edgecolor=path_colors[p % len(path_colors)], facecolor='none', alpha=1, lw=2)
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
ff.setDouble("minSpeed",0.0000)

# data_resolution (in meters)
data_resolution = 10
# size of sub_sim (each independant sub simulation)
sub_sim_shape = (60,80)
# size of the wall (barrier between each independant simulations)
wall_size = min(sub_sim_shape) // 10

shape_multisim = (len(k),1)
# total size of sim
sim_shape = (sub_sim_shape[0]*shape_multisim[0], sub_sim_shape[1]*shape_multisim[1])
# domain_width & domain_height
domain_width = sim_shape[0] * data_resolution
domain_height = sim_shape[1] * data_resolution

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
# fuel_map.fill(fuel_type)
altitude_map = np.zeros(sim_shape)

# Create a list to save simulation params
sim_params = np.zeros(shape_multisim).tolist()

for i in range(shape_multisim[0]):
    # Assign the corresponding fuel to fuel_map
    s = (sub_sim_shape[0] - 2, sub_sim_shape[1] - 2)
    s0 = sub_sim_shape[0] * i + 1
    s1 = sub_sim_shape[0] * (i+1) - 1
    s2 = 1
    s3 = sub_sim_shape[1] * 1 - 1
    # print(s0, s1, s2, s3)
    a = np.random.random(size=s)
    a = np.where(a > k[i], fuel_type, 0)
    # print(a.shape, fuel_map[s0:s1, s2:s3].shape)
    fuel_map[s0:s1, s2:s3] = a

    s2, s3 = 1, int(sub_sim_shape[1] * start_end_zone_pct)
    fuel_map[s0:s1,s2:s3] = fuel_type

    s2, s3 = int(sub_sim_shape[1] * (1 - start_end_zone_pct)), sub_sim_shape[1] - 1
    fuel_map[s0:s1,s2:s3] = fuel_type

    # Compute slices used for set this row of altitude
    s0 = slice(i * sub_sim_shape[0], (i+1) * sub_sim_shape[0])
    s1 = slice(sub_sim_shape[1], sub_sim_shape[1])
    # Generate altitude_map with all the slops
    altMap = 0 #genAltitudeMap(slopes[slope_index], sub_sim_shape, data_resolution)
    # Assign the corresponding slopes to altitude_map
    altitude_map[s0,s1] = altMap

    # Compute ignition point
    ii = (((i+1) * sub_sim_shape[0]) + (i * sub_sim_shape[0])) // 2
    jj = 5

    # Create a dictionnary with current parameters
    one_sim_param = dict(
        ignition = (ii * data_resolution, jj * data_resolution),
        fuel = fuel_type,
        slope = 0,
        pathes = [],
        pathes_time = [],
        speeds = [],
        width = [],
        height = []
    )
    # Assign these params to the matrix containing all parameters
    sim_params[i][0] = one_sim_param

# Add the fuel_map and altitude_map to the firefront layers
ff.addIndexLayer("table", "fuel", 0, 0, 0, domain_width, domain_height, 0, fuel_map)
ff.addScalarLayer("table", "altitude", 0, 0, 0, domain_width, domain_height, 0, altitude_map)

# Start the simulation at timestep 0
ff.execute("\tFireFront[t=0.]")

# Start ignitions with previoulsy computed ignitions points
for fuel_index in range(shape_multisim[0]):
    for slope_index in range(shape_multisim[1]):
        one_sim_param = sim_params[fuel_index][slope_index]
        ipoint = one_sim_param['ignition']
        ff.execute("startFire[loc=(%i,%i,0.);vel=(1.,1.,0.);t=0.]" % (ipoint[0], ipoint[1]))


# Loop over number of timesteps, step by step_size
pathes = []
for i in range(1, nb_steps+1):
    try:
        # Advance timestep by step_size
        print("goTo[t=%f]" % (i*step_size))
        ff.execute("goTo[t=%f]" % (i*step_size))
        pathes.append([])
        # Get pathes from previous execution
        newPathes = printToPathe(ff.execute("print[]"))
        pathes[i-1] += newPathes

    except KeyboardInterrupt:
        # Keyboard interrupt in case simulation take a while and we want to show current state of simulation
        break


# Finally, plot simulations and show stats
plot_simulation(pathes, fuel_map, domain_width, domain_height)
