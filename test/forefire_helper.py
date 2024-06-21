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

def standardRothermelFuelTable():
    return """Index;Rhod;Rhol;Md;Ml;sd;sl;e;Sigmad;Sigmal;stoch;RhoA;Ta;Tau0;Deltah;DeltaH;Cp;Cpa;Ti;X0;r00;Blai;me
111;500.0;500.0;0.15;0.5;2400.0;5700.0;0;0.0;0;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
112;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
121;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
122;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
123;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
124;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
131;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
132;720.0;720.0;0.08;1;5544.0;4766.0;0;0.89;1.79;8.3;1.0;300.0;75590.0;2300000.0;1.6E7;2000.0;1100.0;600.0;0.3;2.5E-5;4.0;0.3
133;720.0;720.0;0.08;1;5544.0;4766.0;0;0.89;1.79;8.3;1.0;300.0;75590.0;2300000.0;1.6E7;2000.0;1100.0;600.0;0.3;2.5E-5;4.0;0.3
141;512.0;512.0;0.08;1;6562;5905;0.46;0.22;0.25;8.3;1.0;300.0;75590.0;2300000.0;1.86E7;1800.0;1000.0;600.0;0.3;2.5E-05;4.0;0.3
142;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
211;500.0;500.0;0.13;0.5;2400.0;5700.0;1;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
212;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
213;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
221;500.0;500.0;0.13;0.5;2400.0;5700.0;0.5;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
222;500.0;500.0;0.13;0.5;2400.0;5700.0;2;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
223;500.0;500.0;0.13;0.5;2400.0;5700.0;2;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
231;500.0;500.0;0.13;0.5;2400.0;5700.0;2;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
241;500.0;500.0;0.13;0.5;2400.0;5700.0;1.6;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
242;500.0;500.0;0.13;0.5;2400.0;5700.0;1.6;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
243;500.0;500.0;0.13;0.5;2400.0;5700.0;1.6;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
244;500.0;500.0;0.13;0.5;2400.0;5700.0;1.6;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
311;512.0;512.0;0.13;0.5;4922.0;2460.0;0.3;0.9;0.67;8.3;1.0;300.0;70000.0;2300000.0;1.86E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
312;512.0;512.0;0.13;0.5;4922.0;2460.0;0.3;0.9;0.67;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
313;500.0;500.0;0.13;0.5;2400.0;5700.0;1.6;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
321;512.0;512.0;0.13;0.5;5905.0;5250.0;0.46;0.54;0.11;8.3;1.0;300.0;70000.0;2300000.0;1.86E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
322;512.0;512.0;0.13;0.5;2460.0;5250.0;1.2;0.8;0.65;8.3;1.0;300.0;70000.0;2300000.0;1.86E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
323;512.0;512.0;0.13;0.5;2460.0;5250.0;1.8;0.8;0.65;8.3;1.0;300.0;70000.0;2300000.0;1.86E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
324;512.0;512.0;0.13;0.5;2460.0;5250.0;1.8;0.8;0.65;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
331;500.0;500.0;1.6;2;2400.0;5700.0;0;10;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
332;500.0;500.0;10;10;2400.0;5700.0;0;10;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
333;512.0;512.0;0.08;0.5;6560.0;5900.0;0.3;0.2;0.05;8.3;1.0;300.0;70000.0;2300000.0;1.86E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
334;512.0;512.0;0.08;0.5;6560.0;5900.0;0.3;0.2;0.05;8.3;1.0;300.0;70000.0;2300000.0;1.86E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
335;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
411;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
412;500.0;500.0;0.13;0.5;2400.0;5700.0;0.1;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
421;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
422;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
423;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
511;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
512;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
521;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
522;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3
523;500.0;500.0;0.13;0.5;2400.0;5700.0;0;0.6;1.28;8.3;1.0;300.0;70000.0;2300000.0;1.5E7;1800.0;1000.0;600.0;0.3;2.5E-5;4.0;0.3"""

def genAltitudeMap(slope_coef, sub_sim_shape, data_resolution):
    """
    Generate a matrix of altitudes given a slope coefficient
    """
    slope = np.linspace(0, 1, sub_sim_shape[1])
    slope = np.repeat(slope, sub_sim_shape[0])
    slope = slope.reshape(sub_sim_shape[1], sub_sim_shape[0]).T
    return slope * slope_coef * (data_resolution / 5)

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

from matplotlib.colors import ListedColormap

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

def fill_random(s, k, value_yes, value_no=0):
    """Generate a randomly filled array."""
    a = np.random.random(size=s)
    return np.where(a > k, value_yes, value_no)


def plot_simulation(pathes, fuel_map, elevation_map, myExtents, scalMap = None):
    """
    Used for plot 4 axis graph, with Heatflux, Fuels, Altitude plotted under simulation, 
    and Statistics for the last axis.
    """
    # Create a figure with 2 axis (2 subplots)
    fig, ax = plt.subplots(figsize=(10,7), dpi=120)

    # Get fuel_map matrix
    if fuel_map is not None:
        fuels = fuel_map
        
        fuels = map_fuel_to_colors(fuels, [82,112, 121, 124, 131, 142, 211, 221, 222, 231, 242, 243, 311, 312,
               313, 321, 322, 323, 324, 331, 332, 333, 411, 512, 521, 523]) # Convert fuels indices to colors
        
        fuel_colors = ['black','indigo', 'aqua', 'orange', 'lime', 'green', 'tan', 'magenta', 'gold',
     'cyan', 'red', 'navy', 'violet', 'black', 'blue', 'olive', 'grey', 'teal', 'maroon', 'yellow', 'lavender', 'silver',
     'turquoise', 'pink', 'purple', 'salmon', 'plum', 'brown', 'orchid', 'white', 'beige']
        # Plot Fuels
        lcmap=ListedColormap(fuel_colors)
        CS = ax.imshow(fuels, cmap=lcmap, interpolation='nearest', origin='lower', extent=myExtents)
       # norm = mcolors.BoundaryNorm(bounds, cmap.N)
        plt.colorbar(CS)

    
    if elevation_map is not None:
        elevation = elevation_map#np.transpose(elevation_map.reshape(elevation_map.shape[0], elevation_map.shape[1], 1))[0]
        
        contour_levels = np.arange(np.min(elevation), np.max(elevation), 200)  # Contours every 200m
        ax.contour(elevation, levels=contour_levels, colors='white', origin='lower', extent=myExtents, linewidths=0.5, linestyles='solid')
    
    if scalMap is not None:
        CS = ax.imshow(scalMap, origin='lower', extent=myExtents)
        plt.colorbar(CS)

    # bounds = [0, 1]
    # cmap = mpl.colors.ListedColormap(['brown', 'green'])
    # norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
    # CS = ax.imshow(fuels, cmap=cmap, interpolation='nearest', origin='lower', extent=(0,domain_width,0,domain_height))
    # # plt.colorbar(plt.cm.ScalarMappable(cmap=cmap, norm=norm), cax=ax)
    # plt.colorbar(CS, norm=norm)

    path_colors = ['red', 'orange', 'yellow', 'white']

    # Plot current firefronts to the first 3 subplots
    for p, path in enumerate(pathes):
        patch = mpatches.PathPatch(path, edgecolor=path_colors[p % len(path_colors)], facecolor='none', alpha=1, lw=2)
        ax.add_patch(patch)
        ax.grid()
        ax.axis('equal')

    ax.grid()
    ax.axis('equal')
    plt.show()



def print_ff_script(file_path):
    """
    Executes each line of a .ff script file using the ff.execute() method,
    after stripping leading and trailing whitespace, including tabs.
    """
    # Open the file with the script
    with open(file_path, 'r') as file:
        # Iterate over each line in the file
        for line in file:
            # Strip leading and trailing whitespace, including tabs, from the line
            clean_line = line.strip()
            # Check if the cleaned line is not empty
            if clean_line:
                # Execute the cleaned line with ff.execute, ensuring no leading/trailing whitespace
                command = f'ff.execute("{clean_line}")'
                print(command)  # This is for demonstration; replace with actual ff.execute(clean_line) in use
                # If you have the ff object with an execute method available, you would call it here:
                # ff.execute(clean_line)
