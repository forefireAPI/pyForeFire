import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches

import pyforefire as forefire


## Simulation Parameters ##
nb_steps = 5                    # The number of step the simulation will execute
step_size = 200                 # The duration (in seconds) between each step
windU = 0                       # The Horizontal wind
windV = 2                       # The Vertical wind
fuel_file_path = './fuels.ff'   # The path of fuel file
fuel_list = [73, 75, 82, 83, 102, 103, 104, 105, 106] # The list of used fuels


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


def plot_simulation(ff, pathes, fuel_map, fuel_list, altitude_map, domain_width, domain_height, sim_params, shape_multisim):
    """
    Used for plot 4 axis graph, with Heatflux, Fuels, Altitude plotted under simulation, 
    and Statistics for the last axis.
    """
    # Create a figure with 4 axis (4 subplots)
    _, axes = plt.subplots(ncols=2, nrows=2, figsize=(10,7), dpi=120)

    # Get heatflux matrix
    heatFlux = np.transpose(ff.getDoubleArray("heatFluxBasic"))[0]

    # Get fuel_map matrix
    fuels = np.transpose(fuel_map.reshape(fuel_map.shape[0], fuel_map.shape[1], 1))[0]
    fuels = map_fuel_to_colors(fuels, fuel_list) # Convert fuels indices to colors

    # Get altitude matrix
    altitude = np.transpose(altitude_map.reshape(altitude_map.shape[0], altitude_map.shape[1], 1))[0]

    # Plot Heatflux
    CS = axes[0][0].imshow(heatFlux, cmap=plt.cm.gray, interpolation='nearest', origin='lower', extent=(0,domain_width,0,domain_height))
    plt.colorbar(CS)

    # Plot Fuels
    CS = axes[0][1].imshow(fuels, cmap=plt.cm.tab10, interpolation='nearest', origin='lower', extent=(0,domain_width,0,domain_height))
    plt.colorbar(CS)

    # Plot Altitude
    CS = axes[1][0].imshow(altitude, cmap=plt.cm.terrain, interpolation='nearest', origin='lower', extent=(0,domain_width,0,domain_height))
    plt.colorbar(CS)

    # Plot current firefronts to the first 3 subplots
    for ax in axes.reshape(4)[:3]:
        for path in pathes:
            patch = mpatches.PathPatch(path, edgecolor='red', facecolor='none', alpha=1)
            ax.add_patch(patch)
            ax.grid()
            ax.axis('equal')

    # This axe is used for stats
    ax = axes[1][1]

    # Get the max speed for each sub simulation
    speeds = [max(param['speeds'][0]) for params in sim_params for param in params]
    speeds = np.array(speeds).reshape(shape_multisim)

    # Get the slope for each sub simulation
    slopes = [param['slope'] for params in sim_params for param in params]
    slopes = np.array(slopes).reshape(shape_multisim)

    # Get the fuel used for each sub simulation
    fuels = [param['fuel'] for params in sim_params for param in params]
    fuels = np.array(fuels).reshape(shape_multisim)

    color_map = [
        'orange',
        'blue',
        'green',
        'red',
        'yellow'
    ] * 2 # Using * 2 for generate a bigger array, but values (colors) are repeated

    # Plot speeds based on slopes
    for x, fuel in enumerate(fuel_list):
        ax.scatter(slopes[x], speeds[x], linewidths=1, alpha=.7,
                    edgecolor='k', label=fuel, s=50, c=color_map[x])

    # Set some plot params and show it
    ax.grid()
    ax.set_xlabel('Slope')
    ax.set_ylabel('Speed')
    ax.legend()
    plt.show()



# Initialize pyforefire module
ff = forefire.ForeFire()

# Set advanced simulation parameters
ff.setString("ForeFireDataDirectory", ".")
ff.setString("fuelsTableFile", fuel_file_path)
ff.setDouble("spatialIncrement",1)
ff.setDouble("minimalPropagativeFrontDepth",20)
ff.setDouble("perimeterResolution",10)
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
data_resolution = 100
# size of sub_sim (each independant sub simulation)
sub_sim_shape = (30,20)
# size of the wall (barrier between each independant simulations)
wall_size = min(sub_sim_shape) // 10
# test with slopes from 0 to 80% step 20%
slopes = range(0,100,20)
shape_multisim = (len(fuel_list),len(slopes))
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
altitude_map = np.zeros(sim_shape)

# Create a list to save simulation params
sim_params = np.zeros(shape_multisim).tolist()

for fuel_index in range(shape_multisim[0]):
    for slope_index in range(shape_multisim[1]):
        # Compute slices used for set this row of fuel
        s0 = slice(fuel_index * sub_sim_shape[0] + wall_size, (fuel_index+1) * sub_sim_shape[0] - wall_size)
        s1 = slice(slope_index * sub_sim_shape[1] + wall_size, (slope_index+1) * sub_sim_shape[1] - wall_size)
        # Assign the corresponding fuel to fuel_map
        fuel_map[s0,s1] = fuel_list[fuel_index]

        # Compute slices used for set this row of altitude
        s0 = slice(fuel_index * sub_sim_shape[0], (fuel_index+1) * sub_sim_shape[0])
        s1 = slice(slope_index * sub_sim_shape[1], (slope_index+1) * sub_sim_shape[1])
        # Generate altitude_map with all the slops
        altMap = genAltitudeMap(slopes[slope_index], sub_sim_shape, data_resolution)
        # Assign the corresponding slopes to altitude_map
        altitude_map[s0,s1] = altMap

        # Compute ignition point
        ii = (((fuel_index+1) * sub_sim_shape[0]) + (fuel_index * sub_sim_shape[0])) // 2
        jj = (((slope_index+1) * sub_sim_shape[1]) + (slope_index * sub_sim_shape[1])) // 2

        # Create a dictionnary with current parameters
        one_sim_param = dict(
            ignition = (ii * data_resolution, jj * data_resolution),
            fuel = fuel_list[fuel_index],
            slope = slopes[slope_index],
            pathes = [],
            pathes_time = [],
            speeds = [],
            width = [],
            height = []
        )
        # Assign these params to the matrix containing all parameters
        sim_params[fuel_index][slope_index] = one_sim_param

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
        # Get pathes from previous execution
        newPathes = printToPathe(ff.execute("print[]"))
        pathes += newPathes
        # Iterate over pathes to store each of them
        for myPath in newPathes:
            px, py = myPath.vertices[0]
            # Get corresponding indices to the sim_params matrix
            I,J = get_sub_domain_indices_from_location(px, py, 0, 0, domain_width, domain_height, shape_multisim)
            # Store pathes and time
            sim_params[I][J]['pathes'].append(myPath.vertices)
            sim_params[I][J]['pathes_time'].append(i*step_size)

    except KeyboardInterrupt:
        # Keyboard interrupt in case simulation take a while and we want to show current state of simulation
        break

# Loop a last time over sim_params to compute stats
for fuel_index in range(len(sim_params)):
    for slope_index in range(len(sim_params[fuel_index])):
        end_pathes = sim_params[fuel_index][slope_index]['pathes'][-1]

        # Get all x OR y coordinates for each pathes
        xs = [x for x, _ in end_pathes]
        ys = [y for _, y in end_pathes]
        # Compute the max (most distant from start)
        max_x = max(xs)
        max_y = max(ys)
        # Get the corresponding indices
        max_x_idx = xs.index(max_x)
        max_y_idx = ys.index(max_y)

        # Compute start and end simulation point (start & most distant from start)
        start_point = sim_params[fuel_index][slope_index]['ignition']
        end_point = (xs[max_x_idx], ys[max_y_idx])

        # Assign the calculated width and height to sim_params
        sim_params[fuel_index][slope_index]['width'].append(maxDiff(xs))
        sim_params[fuel_index][slope_index]['height'].append(maxDiff(ys))

        # Compute the X and Y speed (Horizontal and Vertical)
        speedX = max((end_point[0] - start_point[0]) / sim_params[fuel_index][slope_index]['pathes_time'])
        speedY = max((end_point[1] - start_point[1]) / sim_params[fuel_index][slope_index]['pathes_time'])

        sim_params[fuel_index][slope_index]['speeds'].append((speedX, speedY))


# Finally, plot simulations and show stats
plot_simulation(ff, pathes, fuel_map, fuel_list, altitude_map, 
                domain_width, domain_height, sim_params, 
                shape_multisim)
