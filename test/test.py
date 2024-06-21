import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches

import pyforefire as forefire

from forefire_helper import *

## Simulation Parameters ##
nb_steps = 5                    # The number of step the simulation will execute
step_size = 200                 # The duration (in seconds) between each step
windU = 0                       # The Horizontal wind
windV = 2                       # The Vertical wind
fuel_file_path = './fuels.ff'   # The path of fuel file
fuel_list = [73, 75, 82, 83, 102, 103, 104, 105, 106] # The list of used fuels


data_resolution = 100
sub_sim_shape = (20,20)
wall_size = min(sub_sim_shape) // 10
slopes = range(0,100,20)

shape_multisim = (len(fuel_list),len(slopes))
sim_shape = (1,1,sub_sim_shape[0]*shape_multisim[0], sub_sim_shape[1]*shape_multisim[1])
domain_height = sim_shape[1] * data_resolution
domain_width = sim_shape[0] * data_resolution



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
        fuel_map[0,0,s0,s1] = fuel_list[fuel_index]

        # Compute slices used for set this row of altitude
        s0 = slice(fuel_index * sub_sim_shape[0], (fuel_index+1) * sub_sim_shape[0])
        s1 = slice(slope_index * sub_sim_shape[1], (slope_index+1) * sub_sim_shape[1])
        # Generate altitude_map with all the slops
        altMap = genAltitudeMap(slopes[slope_index], sub_sim_shape, data_resolution)
        # Assign the corresponding slopes to altitude_map
        altitude_map[0,0,s0,s1] = altMap

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



# Initialize pyforefire module
ff = forefire.ForeFire()
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
ff["SWx"] = 0.
ff["SWy"] = 0.
ff["Lx"] = domain_width
ff["Ly"] = domain_height

domain_string = f'FireDomain[sw=({ff["SWx"]},{ff["SWy"]},0);ne=({ff["SWx"] + ff["Lx"]},{ff["SWy"] + ff["Ly"]},0);t=0]'
ff.execute(domain_string)

# Add the required Forefire layers
ff.addLayer("data","altitude","z0")
ff.addLayer("data","windU","windU")
ff.addLayer("data","windV","windV")
ff.addLayer("BRatio","BRatio","BRatio")
ff.addLayer("flux","heatFluxBasic","defaultHeatType")
ff.addLayer("propagation","Rothermel","propagationModel")









# Finally, plot simulations and show stats
plot_simulation(ff, pathes, fuel_map, fuel_list, altitude_map, 
                domain_width, domain_height, sim_params, 
                shape_multisim)
