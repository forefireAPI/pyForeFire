import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import math as m
import pyforefire as forefire
from forefire_helper import printToPathe
###############################################################################
##:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#                    IDEALIZED TEST CASE CURVATURE
##::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: 
## Front propagates with velocity in a curvature dependent fashion for y << domain_height//2
##-----------------------------------------------------------------------------
## Propagation model "CurvatureDriven"-> ROS=Idealizedvv*vv_coeff*(1-Kcurv*curv/sqrt(1+beta*pow(curv,2)));
## - change the constant propagation velocity by setting: 
##      ff["Idealizedvv"]=value
## - change coefficients vv_coeff,Kcurv,beta by editing "VVCoeffTable()"

## To simulate inhomogeneous propagation:
##     1) add rows to the fuel table VVCoeffTable():
##
##    |Index|vv_coeff|Kcurv|beta|
##    |-----|--------|-----|----|
##    |1    |1.0     | 2.0 | 10 |
##    |-----|--------|-----|----|
##    |2    |1.0     | 0.0 |    |   ##!! KCurv=0 -> no curvature effect!!
##    |-----|--------|-----|----|
##      ...    ...     ...  ...
##
##     2) edit the fuelmap using a pattern of "Index" values
##     Ex:
##         fuel_map[:,:,:,:int(.5*sim_shape[1])].fill(valueofIndex1)    
##         fuel_map[:,:,:,int(.5*sim_shape[1]):].fill(valueofIndex2)
###############################################################################
##-----------------------------------------------------------------------------
##  Routine for plotting
##-----------------------------------------------------------------------------
def plot_test(pathes, myExtents):
    """
    Used for plot 4 axis graph, with Heatflux, Fuels, Altitude plotted under simulation, 
    and Statistics for the last axis.
    """
    # Create a figure with 2 axis (2 subplots)
    fig, ax = plt.subplots(figsize=(10,7), dpi=120)

    # Plot current firefronts to the first 3 subplots
    for p, path in enumerate(pathes):
        patch = mpatches.PathPatch(path, edgecolor="Red", facecolor='none', alpha=1, lw=2)
        ax.add_patch(patch)
        ax.grid()
        ax.axis('equal')
    plt.show()
##-----------------------------------------------------------------------------
##  Fuel type table
##-----------------------------------------------------------------------------

def VVCoeffTable():
    return """Index;vv_coeff;Kcurv;beta
1;1.0;14.0;6.0
2;1.0;0.0;1.0"""

##-----------------------------------------------------------------------------
##  Simulation parameters and settings ##
##-----------------------------------------------------------------------------
nb_steps = 10                 # The number of step the simulation will execute
step_size = 20                # The duration (in seconds) of time steps
fuel_type = 1                  # The type of used fuel

##   Initialize pyforefire module
ff = forefire.ForeFire()
##  Fuel settings
ff["fuelsTable"] = VVCoeffTable()
ff["defaultFuelType"]=1
##  ForeFire settings
ff["spatialIncrement"]=0.5
ff["minimalPropagativeFrontDepth"]=10
ff["perimeterResolution"]=5
ff["initialFrontDepth"]=1
ff["relax"]=1.
ff["smoothing"]=100
ff["minSpeed"]=0.0
ff["bmapLayer"]=1
##  Propagation model settings
ff["speed_module"]=1. #Value of the homogeneous propagation speed
ff["propagationModel"] = "CurvatureDriven"

## Total size of simulation domain (meters)
sim_shape = (2000, 4000)
# domain_width & domain_height
domain_height = sim_shape[0]
domain_width = sim_shape[1]
ff["SWx"] = 0.
ff["SWy"] = 0.
ff["Lx"] = domain_width
ff["Ly"] = domain_height

# Init fuel_map 
fuel_map = np.zeros((1, 1) + sim_shape)
fuel_map.fill(fuel_type)
fuel_map[:,:,:,int(.5*sim_shape[1]):].fill(2)   ##NO CURVATURE EFFECT 

##:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
## Shape of the initial fronts is defined by points corrdinates below
##:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
## FRONT 1
sidesize=400 #int
pointxcenter=4*domain_width//10
pointycenter=domain_height//2
x1,y1=pointxcenter-sidesize/2, pointycenter-sidesize/2
x2,y2=pointxcenter-sidesize/2, int(pointycenter+1*sidesize)
x3,y3=pointxcenter, pointycenter+int(.5*sidesize)
x4,y4=pointxcenter+sidesize/2, int(pointycenter+1*sidesize)
x5,y5=pointxcenter+sidesize/2, pointycenter-sidesize/2
x6,y6=pointxcenter, pointycenter

## FRONT 2
pointxxcenter=7*domain_width//10
pointyycenter=domain_height//2
xx1,yy1=pointxxcenter-sidesize/2, pointyycenter-sidesize/2
xx2,yy2=pointxxcenter-sidesize/2, int(pointyycenter+1*sidesize)
xx3,yy3=pointxxcenter, pointyycenter+int(.5*sidesize)
xx4,yy4=pointxxcenter+sidesize/2, int(pointyycenter+1*sidesize)
xx5,yy5=pointxxcenter+sidesize/2, pointyycenter-sidesize/2
xx6,yy6=pointxxcenter, pointyycenter

##-----------------------------------------------------------------------------
##  SIMULATION STARTS
##-----------------------------------------------------------------------------        
domain_string = f'FireDomain[sw=({ff["SWx"]},{ff["SWy"]},0);ne=({ff["SWx"] + ff["Lx"]},{ff["SWy"] + ff["Ly"]},0);t=0]'
ff.execute(domain_string)

# Add the required Forefire layers
ff.addLayer("BRatio","BRatio","BRatio")
ff.addLayer("flux","heatFluxBasic","defaultHeatType")
ff.addLayer("propagation",ff["propagationModel"],"propagationModel")
ff.addIndexLayer("table", "fuel", float(ff["SWx"]), float(ff["SWy"]), 0, domain_width, domain_height, 0, fuel_map)


ff.execute(f"\tFireFront[id=2;domain=0;t=0]")
ff.execute(f"\t\tFireNode[domain=0;loc=({x1},{y1},0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute(f"\t\tFireNode[domain=0;loc=({x2},{y2},0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute(f"\t\tFireNode[domain=0;loc=({x3},{y3},0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute(f"\t\tFireNode[domain=0;loc=({x4},{y4},0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute(f"\t\tFireNode[domain=0;loc=({x5},{y5},0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute(f"\t\tFireNode[domain=0;loc=({x6},{y6},0);vel=(0,0,0);t=0;state=init;frontId=2]")


ff.execute(f"\tFireFront[id=3;domain=0;t=0]")
ff.execute(f"\t\tFireNode[domain=0;loc=({xx1},{yy1},0);vel=(0,0,0);t=0;state=init;frontId=3]")
ff.execute(f"\t\tFireNode[domain=0;loc=({xx2},{yy2},0);vel=(0,0,0);t=0;state=init;frontId=3]")
ff.execute(f"\t\tFireNode[domain=0;loc=({xx3},{yy3},0);vel=(0,0,0);t=0;state=init;frontId=3]")
ff.execute(f"\t\tFireNode[domain=0;loc=({xx4},{yy4},0);vel=(0,0,0);t=0;state=init;frontId=3]")
ff.execute(f"\t\tFireNode[domain=0;loc=({xx5},{yy5},0);vel=(0,0,0);t=0;state=init;frontId=3]")
ff.execute(f"\t\tFireNode[domain=0;loc=({xx6},{yy6},0);vel=(0,0,0);t=0;state=init;frontId=3]")

#ff.execute(f"startFire[loc=({pointxcenter},{pointycenter},0.);t=0.0]")


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

    except KeyboardInterrupt:
        # Keyboard interrupt in case simulation take a while and we want to show current state of simulation
        break

fact=0.2
ffplotExtents=(x1-fact*domain_width,x5+fact*domain_width,y1-fact*domain_height,y5+fact*domain_height)
plot_test(pathes,ffplotExtents)

