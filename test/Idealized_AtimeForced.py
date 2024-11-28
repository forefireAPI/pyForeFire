#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 10:23:07 2024

@author: baggio_r2
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import pyforefire as pyff
import xarray as xr


def plot_test(pathes, myExtents,times,velocity,fs=15):
    """
    Used for plot 4 axis graph, with Heatflux, Fuels, Altitude plotted under simulation, 
    and Statistics for the last axis.
    """
    # Create a figure with 2 axis (2 subplots)
    fig, ax = plt.subplots(1,2, figsize=(10,7), dpi=120)

    # Plot current firefronts to the first 3 subplots
    for p, path in enumerate(pathes):
        patch = mpatches.PathPatch(path, edgecolor="Red", facecolor='none', alpha=1, lw=2)
        ax[0].add_patch(patch)
        ax[0].grid()
        ax[0].axis('equal')

    ax[1].plot(times,bournawt,'o',label="Simulated fronts")
    ax[1].plot(times, np.pi*np.power((velocity*np.array(times)),2),c="Red",ls="--",label=r"${\pi}R^2$")
    #ax[1].hlines(theoryA,xmin=0,xmax[1]=totTime,ls=":",color="Grey")
    ax[1].set_xlabel("Time",fontsize=1.5*fs)
    ax[1].set_ylabel("Spanned Area",fontsize=1.5*fs)
    plt.legend(fontsize=fs)
    plt.tight_layout()
    plt.show()
##-----------------------------------------------------------------------------
##  Fuel type table
##-----------------------------------------------------------------------------
def VVCoeffTable():
    return """Index;vv_coeff
1;2
2;4
3;6
4;8"""

##-----------------------------------------------------------------------------
##  Simulation parameters and settings ##
##-----------------------------------------------------------------------------
## 
nb_steps = 2 #200             # The number of step the simulation will execute
step_size = 20 #1               # The duration (in seconds) of time steps
fuel_type = 1                   # The type of used fuel by default (Index in VVCoeffTable() )

##   Initialize pyforefire module
ff = pyff.ForeFire()

##  Fuel settings
ff["fuelsTable"] = VVCoeffTable()
ff["defaultFuelType"]=1.
##  ForeFire settings
ff["spatialIncrement"]=0.6
ff["minimalPropagativeFrontDepth"]=1
ff["perimeterResolution"]=4
ff["initialFrontDepth"]=1

ff["relax"]=1.
ff["smoothing"]=100
ff["minSpeed"]=0.000
ff["bmapLayer"]=1
##  Propagation model settings
ff["speed_module"]=1.  ## spreading velocity (meters seconds-1)
ff["propagationModel"] = "BMapLoggerForANNTraining"
ff["FFANNPropagationModelPath"] = "/Users/filippi_j/soft/pyForeFire/test/empty.ffann"
ff["FFBMapLoggerCSVPath"] = "/Users/filippi_j/soft/pyForeFire/test/RNNdata.csv"
ff["LookAheadDistanceForeTimeGradientDataLayer"] = 10    
## Total size of simulation domain (meters)
sim_shape = (3000, 2000)
ff["atmoNX"]=100
ff["atmoNY"]=50

data_resolution = 1
domain_width = sim_shape[0]
domain_height = sim_shape[1]


ff["SWx"] = 0.
ff["SWy"] = 0.
ff["Lx"] = domain_width
ff["Ly"] = domain_height

# Init fuel_map matrix
fuel_map = np.zeros((1, 1) + sim_shape)
# Fill each quadrant with specific values
half_x, half_y = sim_shape[0] // 2, sim_shape[1] // 2
fuel_map[:, :, :half_x, :half_y] = 1
fuel_map[:, :, :half_x, half_y:] = 2
fuel_map[:, :, half_x:, :half_y] = 4
fuel_map[:, :, half_x:, half_y:] = 3
##:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
## Uncomment below for non homogeneous surface spreading
##:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# fuel_map[:,:,int(.5*sim_shape[0]),:].fill(1)    
# fuel_map[:,:,int(.5*sim_shape[0]):,:].fill(2)

##-----------------------------------------------------------------------------
##  SIMULATION STARTS
##-----------------------------------------------------------------------------    

at_file_path = "ForeFire.0.nc"
lcp = xr.open_dataset(at_file_path)
at_map = np.expand_dims(np.expand_dims(lcp.arrival_time_of_front.data, axis=0), axis=0)

at_map[at_map <=0] = 0

print(np.min(at_map))

lcp.close()


domain_string = f'FireDomain[sw=({ff["SWx"]},{ff["SWy"]},0);ne=({ff["SWx"] + ff["Lx"]},{ff["SWy"] + ff["Ly"]},0);t=0]'
ff.execute(domain_string)

## Add the required Forefire layers
ff.addLayer("BRatio","BRatio","BRatio")  ## Time of arrival matrix 
ff.addLayer("propagation",ff["propagationModel"],"propagationModel") ## Propagation model
ff.addIndexLayer("table", "fuel", float(ff["SWx"]), float(ff["SWy"]), 0, domain_width, domain_height, 0, fuel_map) ## Fuel map layer
ff.addScalarLayer("data", "forced_arrival_time_of_front", float(ff["SWx"]), float(ff["SWy"]), 0, domain_width, domain_height, 0, at_map) 

## "Ignition" point
pointxcenter=domain_width//2
pointycenter=domain_height//2
ff.execute(f"startFire[loc=({pointxcenter},{pointycenter},0.);t=0.0]")

# Loop over number of timesteps, step by step_size
pathes = [] ##list to store fronts
bournawt=[] ##list to store spanned area
times=[]
errort=[]   ##list to store relative error with time 
##-----------------------------------------------------------------------------

for i in range(1, nb_steps+1):
    try:
        # Advance timestep by step_size
        ff.execute("goTo[t=%f]" % (i*step_size))
        # Get pathes from previous execution
        newPathes = pyff.helpers.printToPathe(ff.execute("print[]"))
        pathes += newPathes
        times.append(i*step_size)

    except KeyboardInterrupt:
        # Keyboard interrupt in case simulation take a while and we want to show current state of simulation
        break
    
ff.execute("plot[parameter=speed;filename=at2.png;cmap=viridis;range=(0,10);histogram=true]")
ffplotExtents =(float(ff["SWx"]),float(ff["SWx"]) + float(ff["Lx"]),float(ff["SWy"]),float(ff["SWy"]) + float(ff["Ly"]))
#ff.execute("save[parameter=arrival_time;filename=at.png;cmap=viridis;histogram=true]")
at=ff.getDoubleArray("BMap")[0,0,:,:]
pyff.helpers.plot_simulation(pathes,None ,None,  ffplotExtents ,scalMap=at)


