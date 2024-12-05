import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches

import pyforefire as forefire

from forefire_helper import *

## Simulation Parameters ##
nb_steps = 5  # The number of steps the simulation will execute
step_size = 200  # The duration (in seconds) between each step
windU = 0  # The Horizontal wind
windV = 2  # The Vertical wind
fuel_file_path = './fuels.ff'  # The path of fuel file
fuel_list = [73, 75, 82, 83, 102, 103, 104, 105, 106]  # The list of used fuels

data_resolution = 100
sub_sim_shape = (20, 20)
wall_size = min(sub_sim_shape) // 10
slopes = range(0, 100, 20)

shape_multisim = (len(fuel_list), len(slopes))
sim_shape = (1, 1, sub_sim_shape[0] * shape_multisim[0], sub_sim_shape[1] * shape_multisim[1])
domain_height = sim_shape[2] * data_resolution
domain_width = sim_shape[3] * data_resolution

# Init fuel_map and altitude_map with zeros
fuel_map = np.zeros(sim_shape)
altitude_map = np.zeros(sim_shape)

# Create a list to save simulation params
sim_params = [[None] * len(slopes) for _ in range(len(fuel_list))]



# Initialize pyforefire module
ff = forefire.ForeFire()
ff["ForeFireDataDirectory"] = "."
ff["fuelsTable"] = standardRothermelFuelTable()
ff["spatialIncrement"] = 1.0
ff["minimalPropagativeFrontDepth"] = 20.0
ff["perimeterResolution"] = 10.0
ff["atmoNX"] = 100
ff["atmoNY"] = 100
ff["initialFrontDepth"] = 5.0
ff["relax"] = 0.1
ff["smoothing"] = 100.0
ff["z0"] = 0.0
ff["windU"] = windU  # Horizontal
ff["windV"] = windV  # Vertical
ff["defaultFuelType"] = 1
ff["bmapLayer"] = 1
ff["defaultHeatType"] = 0
ff["nominalHeatFlux"] = 100000.0
ff["burningDuration"] = 100.0
ff["maxFrontDepth"] = 50.0
ff["minSpeed"] = 0.0
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




for fuel_index in range(shape_multisim[0]):
    for slope_index in range(shape_multisim[1]):
        # Compute slices for setting this section of fuel map and altitude map
        s0 = slice(fuel_index * sub_sim_shape[0] + wall_size, (fuel_index+1) * sub_sim_shape[0] - wall_size)
        s1 = slice(slope_index * sub_sim_shape[1] + wall_size, (slope_index+1) * sub_sim_shape[1] - wall_size)

        # Assign the corresponding fuel to the fuel_map
        fuel_map[0, 0, s0, s1] = fuel_list[fuel_index]

        # Generate altitude map for this slope
        altMap = genAltitudeMap(slopes[slope_index], sub_sim_shape, data_resolution)

        # Compute slices for setting this section of altitude
        s0 = slice(fuel_index * sub_sim_shape[0], (fuel_index+1) * sub_sim_shape[0])
        s1 = slice(slope_index * sub_sim_shape[1], (slope_index+1) * sub_sim_shape[1])

        # Assign the generated altitude map to the altitude_map
        altitude_map[0, 0, s0, s1] = altMap

        # Calculate the center of each section for ignition point
        ii = (s0.start + s0.stop) // 2
        jj = (s1.start + s1.stop) // 2

        # Store simulation parameters
        sim_params[fuel_index][slope_index] = {
            'ignition': (ii * data_resolution, jj * data_resolution),
            'fuel': fuel_list[fuel_index],
            'slope': slopes[slope_index],
            'pathes': [],
            'pathes_time': [],
            'speeds': [],
            'width': [],
            'height': []
        }

# Initialize the ForeFire simulation object
ff = forefire.ForeFire()
ff.setString("ForeFireDataDirectory", ".")
ff.setString("fuelsTableFile", fuel_file_path)
ff.setInt("atmoNX", sim_shape[3])
ff.setInt("atmoNY", sim_shape[2])
ff["SWx"] = 0.
ff["SWy"] = 0.
ff["Lx"] = domain_width
ff["Ly"] = domain_height

# Add the fuel_map and altitude_map to the firefront layers
ff.addIndexLayer("table", "fuel", 0, 0, 0, domain_width, domain_height, 0, fuel_map)
ff.addScalarLayer("table", "altitude", 0, 0, 0, domain_width, domain_height, 0, altitude_map)


# Start ignitions with previously computed ignition points
for fuel_index in range(shape_multisim[0]):
    for slope_index in range(shape_multisim[1]):
        one_sim_param = sim_params[fuel_index][slope_index]
        ipoint = one_sim_param['ignition']
        fsString=f"startFire[loc=({ipoint[0]},{ipoint[1]},0.);vel=(1.,1.,0.);t=0.]"
        print(fsString)
        ff.execute(fsString)
        

# Loop over number of timesteps
pathes = []
for i in range(1, nb_steps + 1):
    print(f"goTo[t={i * step_size}]")
    ff.execute(f"goTo[t={i * step_size}]")  # Advance timestep
    # Assuming 'printToPathe' correctly parses the output of 'ff.execute("print[]")'
    #print(ff.execute("print[]"))
    newPathes = printToPathe(ff.execute("print[]"))
    pathes.extend(newPathes)

    # Store each path with its simulation parameters
    for myPath in newPathes:
 
        px, py = myPath.vertices[0]  # First vertex is assumed to be the start or reference point
      
 
        I, J = get_multi_sub_domain_indices_from_location(px, py, 0, 0, domain_width, domain_height, shape_multisim)
        sim_params[I][J]['pathes'].append(myPath.vertices)
        sim_params[I][J]['pathes_time'].append(i * step_size)

# Compute statistics for each simulation parameter set
for fuel_index in range(len(sim_params)):
    for slope_index in range(len(sim_params[fuel_index])):
        if sim_params[fuel_index][slope_index]['pathes']:
            end_pathes = sim_params[fuel_index][slope_index]['pathes'][-1]

            xs = [x for x, _ in end_pathes]
            ys = [y for _, y in end_pathes]

            max_x = max(xs)
            max_y = max(ys)

            max_x_idx = xs.index(max_x)
            max_y_idx = ys.index(max_y)

            start_point = sim_params[fuel_index][slope_index]['ignition']
            end_point = (xs[max_x_idx], ys[max_y_idx])

            sim_params[fuel_index][slope_index]['width'].append(max(xs) - min(xs))
            sim_params[fuel_index][slope_index]['height'].append(max(ys) - min(ys))

            if sim_params[fuel_index][slope_index]['pathes_time'][-1] != 0:
                speedX = (end_point[0] - start_point[0]) / sim_params[fuel_index][slope_index]['pathes_time'][-1]
                speedY = (end_point[1] - start_point[1]) / sim_params[fuel_index][slope_index]['pathes_time'][-1]
                sim_params[fuel_index][slope_index]['speeds'].append((speedX, speedY))

# Finally, plot simulations and show stats
ffplotExtents =(float(ff["SWx"]),float(ff["SWx"]) + float(ff["Lx"]),float(ff["SWy"]),float(ff["SWy"]) + float(ff["Ly"]))
 
def plot_multi_simulation(ff, pathes, fuel_map, fuel_list, altitude_map, domain_width, domain_height, sim_params, shape_multisim):
    """
    Plots a 4-axis graph with Heatflux, Fuels, Altitude under simulation, 
    and Statistics for the last axis. Assumes that sim_params is a 2D list of dictionaries.
    """
    # Create a figure with 4 subplots
    fig, axes = plt.subplots(ncols=2, nrows=2, figsize=(10, 7), dpi=120)
    axes = axes.flatten()  # Flatten for easier indexing

    # Prepare data
    heatFlux = ff.getDoubleArray("heatFluxBasic")[0,0,:,:]
    fuels_reshaped = ff.getDoubleArray("fuel")[0,0,:,:]
    altitude_reshaped = altitude_map[0,0,:,:]
    fuels_colored = map_fuel_to_colors(fuels_reshaped, fuel_list)  # Convert fuel indices to colors

    # Plotting data matrices
    for ax, data, cmap, title in zip(axes[:3], [heatFlux, fuels_colored, altitude_reshaped], [plt.cm.gray, plt.cm.tab10, plt.cm.terrain], ['Heatflux', 'Fuels', 'Altitude']):
        CS = ax.imshow(data, cmap=cmap, interpolation='nearest', origin='lower', extent=(0, domain_width, 0, domain_height))
        fig.colorbar(CS, ax=ax)
        ax.set_title(title)

    # Plot paths on the first three subplots
    for ax in axes[:3]:
        for path in pathes:
            patch = mpatches.PathPatch(path, edgecolor='red', facecolor='none', lw=0.5)
            ax.add_patch(patch)
        ax.grid(True)
        ax.axis('equal')

    # Statistics plot
    stats_ax = axes[3]
    speeds = [max(param['speeds'][0]) for params in sim_params for param in params if param['speeds']]
    slopes = [param['slope'] for params in sim_params for param in params]
    fuels_used = [param['fuel'] for params in sim_params for param in params]

    # Scatter plot for speeds based on slopes with different colors for each fuel
    colors = ['orange', 'blue', 'green', 'red', 'yellow'] * ((len(fuel_list) // 5) + 1)  # Ensure enough colors
    for idx, (slope, speed, fuel) in enumerate(zip(slopes, speeds, fuels_used)):
        stats_ax.scatter(slope, speed, color=colors[fuel_list.index(fuel)], label=f'Fuel {fuel}' if idx % shape_multisim[0] == 0 else "")

    # Formatting statistics plot
    stats_ax.grid(True)
    stats_ax.set_xlabel('Slope')
    stats_ax.set_ylabel('Speed')
    stats_ax.legend(title="Fuel Types", loc='upper right')
    plt.tight_layout()
    plt.show()

# Note: map_fuel_to_colors() must be defined to map fuel indices to colors, which is assumed to be already implemented.


#plot_simulation(pathes,ff.getDoubleArray("fuel")[0,0,:,:] ,ff.getDoubleArray("altitude")[0,0,:,:],  ffplotExtents ,scalMap=ff.getDoubleArray("BMap")[0,0,:,:])
plot_multi_simulation(ff, pathes, fuel_map, fuel_list, altitude_map,                 domain_width, domain_height, sim_params,                 shape_multisim)

