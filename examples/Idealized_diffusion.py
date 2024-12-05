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


###############################################################################
##:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#                    IDEALIZED TEST CASE DIFFUSION
##::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: 
## Front propagates at constant speed in an homogeneous environment
##-----------------------------------------------------------------------------
## Propagation model "IsotropicFuel"-> ROS = speed_module*vv_coeff
## - change the constant propagation velocity by setting: 
##      ff["speed_module"]=value
## - change coefficient vv_coeff by editing "VVCoeffTable()"

## To simulate inhomogeneous propagation:
##     1) add rows to the fuel table VVCoeffTable():
##    ________________  
##    |Index|vv_coeff|
##    |-----|--------|  
##    |1    |1.0     |
##    |-----|--------|
##    |2    |0.5     |
##    |-----|--------|
##      ...    ...
##
##     2) edit the fuelmap using a pattern of "Index" values
##     Ex:
##         fuel_map[:,:,:,:int(.5*sim_shape[1])].fill(valueofIndex1)    
##         fuel_map[:,:,:,int(.5*sim_shape[1]):].fill(valueofIndex2)
###############################################################################
###############################################################################
##-----------------------------------------------------------------------------
##  Routine for plotting
##-----------------------------------------------------------------------------
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
1;1.0
2;0.5"""

##-----------------------------------------------------------------------------
##  Simulation parameters and settings ##
##-----------------------------------------------------------------------------
## 
nb_steps = 20  #200             # The number of step the simulation will execute
step_size = 10 #1               # The duration (in seconds) of time steps
fuel_type = 1                   # The type of used fuel by default (Index in VVCoeffTable() )

##   Initialize pyforefire module
ff = pyff.ForeFire()

##  Fuel settings
ff["fuelsTable"] = VVCoeffTable()
ff["defaultFuelType"]=1.
##  ForeFire settings
ff["spatialIncrement"]=0.2
ff["minimalPropagativeFrontDepth"]=1.
ff["perimeterResolution"]=1 
ff["initialFrontDepth"]=1
ff["relax"]=1.
ff["smoothing"]=100
ff["minSpeed"]=0.000
ff["bmapLayer"]=1
##  Propagation model settings
ff["speed_module"]=1.  ## spreading velocity (meters seconds-1)
ff["propagationModel"] = "IsotropicFuel"

## Total size of simulation domain (meters)
sim_shape = (2000, 2000)
data_resolution = 1
domain_width = sim_shape[0]
domain_height = sim_shape[1]
ff["SWx"] = 0.
ff["SWy"] = 0.
ff["Lx"] = domain_width
ff["Ly"] = domain_height

# Init fuel_map matrix
fuel_map = np.zeros((1, 1) + sim_shape)
fuel_map.fill(fuel_type)
##:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
## Uncomment below for non homogeneous surface spreading
##:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# fuel_map[:,:,int(.5*sim_shape[0]),:].fill(1)    
# fuel_map[:,:,int(.5*sim_shape[0]):,:].fill(2)

##-----------------------------------------------------------------------------
##  SIMULATION STARTS
##-----------------------------------------------------------------------------    
domain_string = f'FireDomain[sw=({ff["SWx"]},{ff["SWy"]},0);ne=({ff["SWx"] + ff["Lx"]},{ff["SWy"] + ff["Ly"]},0);t=0]'
ff.execute(domain_string)

## Add the required Forefire layers
ff.addLayer("BRatio","BRatio","BRatio")  ## Time of arrival matrix 
ff.addLayer("propagation",ff["propagationModel"],"propagationModel") ## Propagation model
ff.addIndexLayer("table", "fuel", float(ff["SWx"]), float(ff["SWy"]), 0, domain_width, domain_height, 0, fuel_map) ## Fuel map layer

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
##  declare the implied v_coeff for surface check (only for homogeneous spreading!)
v_coeff=float(ff["speed_module"])
##-----------------------------------------------------------------------------
for i in range(1, nb_steps+1):
    try:
        # Advance timestep by step_size
        
        ff.execute("goTo[t=%f]" % (i*step_size))
        # Get pathes from previous execution
        newPathes = pyff.helpers.printToPathe(ff.execute("print[]"))
        pathes += newPathes
        bmap=ff.getDoubleArray("BMap")

        burnrbool = np.logical_not(np.isinf(bmap))
    # Count the True values in non_inf array
        burnr = np.sum(burnrbool*np.power(float(ff["minimalPropagativeFrontDepth"]),2))
        bournawt.append(burnr)
    ## Area of circle
        circlesurf=np.pi*np.power((i*step_size)*float(ff["speed_module"])*v_coeff,2)
        error=100*np.abs(burnr-circlesurf)/circlesurf
        errort.append(np.abs(burnr-circlesurf)/circlesurf)
        print(f"goTo[t={(i*step_size)}]   Surface Area: {burnr:.0f}  Circle pi*(velocity*time)^2: {circlesurf:.0f}  %error: {error:.0f} %")
        times.append(i*step_size)

    except KeyboardInterrupt:
        # Keyboard interrupt in case simulation take a while and we want to show current state of simulation
        break
    
##-----------------------------------------------------------------------------
##  SIMULATION ENDS
##-----------------------------------------------------------------------------  
    
##-----------------------------------------------------------------------------
##   Plot the simulated Fronts and Evolution of spreading area vs circle pi*(time*velocity)¨2
##-----------------------------------------------------------------------------
velcof=v_coeff
x1=pointxcenter-velcof*float(ff["speed_module"])*nb_steps*step_size
y1=x1
x2=pointxcenter+velcof*float(ff["speed_module"])*nb_steps*step_size
y2=x2
fact=0.2
ffplotExtents=(x1-fact*domain_width,x2+fact*domain_width,y1-fact*domain_height,y2+fact*domain_height)
velocity=float(ff["speed_module"])*velcof
#totTime=step_size*nb_steps
totTime=times[-1]
theoryA=np.pi*np.power(velocity*totTime,2)
print(f"theoryA is {theoryA}")
plot_test(pathes, ffplotExtents,times,velocity,fs=15)