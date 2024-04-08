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

def plot_simulation(pathes, fuel_map, elevation_map, myExtents, scalMap = None):
    """
    Used for plot 4 axis graph, with Heatflux, Fuels, Altitude plotted under simulation, 
    and Statistics for the last axis.
    """
    # Create a figure with 2 axis (2 subplots)
    fig, ax = plt.subplots(figsize=(10,7), dpi=120)

    # Get fuel_map matrix
    if fuel_map is not None:
        fuels = fuel_map#np.transpose(fuel_map.reshape(fuel_map.shape[0], fuel_map.shape[1], 1))[0]
        
        fuels = map_fuel_to_colors(fuels, [112, 121, 124, 131, 142, 211, 221, 222, 231, 242, 243, 311, 312,
               313, 321, 322, 323, 324, 331, 332, 333, 411, 512, 521, 523]) # Convert fuels indices to colors
        
        fuel_colors = ['indigo', 'aqua', 'orange', 'lime', 'green', 'tan', 'magenta', 'gold',
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

# Example usage




landscape_file_path = "/Users/filippi_j/soft/pyForeFire/test/sample8DIRwind.nc"
#landscape_file_path = "/Users/filippi_j/soft/pyForeFire/test/sampleUVCoeffLandscape.nc"
fuel_file_path = '/Users/filippi_j/soft/firefront/Examples/aullene/fuels.ff'  

ff = forefire.ForeFire()

ff["projection"] = "EPSG:32632"

ff["fuelsTableFile"]= fuel_file_path
ff["propagationModel"] = "Rothermel"

ff["fuelsTableFile"]= fuel_file_path
ff["spatialIncrement"] = 3
ff["perimeterResolution"] = 10
ff["minimalPropagativeFrontDepth"] = 20

ff["TroisPourcent.windFactor"] = 0.1

ff["relax"] = 0.5
ff["minSpeed"] = 0.30
ff["propagationSpeedAdjustmentFactor"] = 1
ff["defaultHeatType"] = 0

ff["bmapLayer"] = 1

testRunMode = "Instructions"

if testRunMode == "Script":
    ff.execute(f'loadData[{landscape_file_path};2009-07-24T11:37:39Z]')
    print(ff.execute("print[]"))


if testRunMode == "Instructions":
    
    lcp = xr.open_dataset(landscape_file_path)
    dom = lcp.domain.attrs    

    fuel_map = lcp.fuel.data
    altitude_map = lcp.altitude.data
    wind_map = lcp.wind.data
    windU=wind_map[0:1,:,:,:]
    windV=wind_map[1:2,:,:,:]
    
    niN = 1024*10
    njN = 1024*10
    niNW = 1024*10
    njNW = 1024*10
    
   # fuel_map = 323 * np.ones((1,1,njN,niN),dtype=np.uint16)
   # altitude_map = 30 * np.ones((1,1,njN,niN),dtype=np.uint16)
   # windU = np.ones((1,2,njNW,niNW),dtype=np.float16)
   # windV = np.ones((1,2,njNW,niNW),dtype=np.float16)    
    
    
    ff.setString("ISOdate", "2009-07-24T11:37:39Z")

    date_obj = datetime.strptime(ff.getString("ISOdate"), "%Y-%m-%dT%H:%M:%SZ")
    secs = date_obj.hour * 3600 + date_obj.minute * 60 + date_obj.second
    year = date_obj.year
    start_of_year = datetime(year, 1, 1)
    yday = (date_obj - start_of_year).days + 1
    
    ff.setInt("refYear", year)
    ff.setInt("refDay", yday)
    ff.setInt("refTime", secs)
    
    ff["SWx"] = float(dom["SWx"])
    ff["SWy"] = float(dom["SWy"])
    ff["Lx"] = float(dom["Lx"])
    ff["Ly"] = float(dom["Ly"])
    
    
    domString = f'FireDomain[sw=({dom["SWx"]},{dom["SWy"]},0);ne=({dom["SWx"] + dom["Lx"]},{dom["SWy"] + dom["Ly"]},0);t=0]'
    ff.execute(domString)
    
    

    ff.addLayer("propagation",ff["propagationModel"],"propagationModel")
    ff.addIndexLayer("table", "fuel", dom["SWx"], dom["SWy"], 0, dom["Lx"], dom["Ly"], 0, fuel_map)
    ff.addScalarLayer("data", "altitude", dom["SWx"], dom["SWy"], 0, dom["Lx"], dom["Ly"], 0, altitude_map)
    
    

    
    makeUVscal = False
    if makeUVscal:
#       if wind was a 8 coeffs :
#       superWindU= wind_map[0:1, [0, 2], :, :]/10
#       superWindV= wind_map[1:2, [0, 2], :, :]/10
       
       windU[:,0,:,:]= 20  # wind potential along U for U
       windV[:,1,:,:]= 20  # wind potential along V for V
       windU[:,1,:,:]= 0  # wind potential along V for U
       windV[:,0,:,:]= 0  # wind potential along U for V
    
    
    ff.execute(f'loadData[/Users/filippi_j/soft/pyForeFire/test/justWind.nc]')
    ff.addScalarLayer("windScalDir", "windU", dom["SWx"], dom["SWy"], 0, dom["Lx"], dom["Ly"], 0, windU)
    ff.addScalarLayer("windScalDir", "windV", dom["SWx"], dom["SWy"], 0, dom["Lx"], dom["Ly"], 0, windV)


#ff.addLayer("flux","heatFluxBasic","defaultHeatType")

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
        newPathes = printToPathe(ff.execute("print[]"))
        ff.execute(f"trigger[wind;loc=(0.,0.,0.);vel=({herex},{herey},0);t=0.]")
        ff.execute("step[dt=%f]" % (step_size))
        pathes += newPathes
        print("Iteration ",i,"/",nb_steps, " angle ", angle_deg)
        
        
    except KeyboardInterrupt:
        # Keyboard interrupt in case simulation take a while and we want to show current state of simulation
        break

end_time = time.time()

# Calculate the total duration
duration = end_time - start_time

# Finally, plot simulations and show stats
ffplotExtents =(float(ff["SWx"]),float(ff["SWx"]) + float(ff["Lx"]),float(ff["SWy"]),float(ff["SWy"]) + float(ff["Ly"]))
 
print(ffplotExtents,f"Total time taken: {duration} seconds")
plot_simulation(pathes,ff.getDoubleArray("fuel")[0,0,:,:] ,ff.getDoubleArray("altitude")[0,0,:,:],  ffplotExtents ,scalMap=ff.getDoubleArray("BMap")[0,0,:,:])
