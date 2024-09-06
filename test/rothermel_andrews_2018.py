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
import seaborn as sns
import math as m
import pyforefire as forefire
from forefire_helper import *


def plot_test(pathes, fuel_map):
    """
    Used for plot 4 axis graph, with Heatflux, Fuels, Altitude plotted under simulation, 
    and Statistics for the last axis.
    """
    # Create a figure with 2 axis (2 subplots)
    fig, ax = plt.subplots(figsize=(10,7), dpi=120)

    path_colors = ['red', 'orange', 'yellow', 'white']

    colors = sns.color_palette("flare", n_colors=len(pathes))

    # Plot current firefronts to the first 3 subplots
    plt.imshow(fuel_map[0, 0], alpha=0.25)
    for p, path in enumerate(pathes):
        patch = mpatches.PathPatch(path, edgecolor=colors[p], facecolor='none', alpha=1, lw=2)
        ax.add_patch(patch)
        ax.grid()
        ax.axis('equal')

    ax.grid()
    ax.axis('equal')
    plt.show()

##-----------------------------------------------------------------------------
##  Simulation parameters and settings ##
##-----------------------------------------------------------------------------
nb_steps = 10              # The number of step the simulation will execute
step_size = 10              # The duration (in seconds) between each step

##   Initialize pyforefire module
ff = forefire.ForeFire()

##  Fuel settings
# ff["fuelsTable"] = RothermelAndrews2018FuelTable()
# ff["propagationModel"] = "RothermelAndrews2018"
ff["fuelsTable"] = standardRothermelFuelTable()
ff["propagationModel"] = "Rothermel"

##  ForeFire settings
ff["spatialIncrement"] = 1.
ff["minimalPropagativeFrontDepth"] = 1
ff["perimeterResolution"] = 10
ff["initialFrontDepth"] = 1
ff["relax"] = 1.
ff["smoothing"] = 100
ff["minSpeed"] = 0.000
ff["bmapLayer"] = 1
ff["windU"] = 20.0 # Horizontal
ff["windV"] = 20.0 # Vertical

## Total size of simulation domain (meters)
sim_shape = (2000, 2000)
# domain_width & domain_height
domain_height = sim_shape[0]
domain_width = sim_shape[1]
ff["SWx"] = 0.
ff["SWy"] = 0.
ff["Lx"] = domain_width
ff["Ly"] = domain_height

# Init fuel_map matrix
fuel_map = 141 * np.ones((1, 1) + sim_shape)
# fuel_map[:, :, :domain_height // 1, :domain_width // 2] = 112

## Shape of the initial front is defined by points corrdinates below
side1=1800  #length of outer side
side2=1100  #length of inner side
pointxcenter=domain_width//2
pointycenter=domain_height//2
h1, w1 = 50, 50
xp1,yp1 = pointxcenter, pointycenter + h1
xp2,yp2 = pointxcenter + w1, pointycenter
xp3,yp3 = pointxcenter - w1, pointycenter

##-----------------------------------------------------------------------------
##  SIMULATION STARTS
##-----------------------------------------------------------------------------       

domain_string = f'FireDomain[sw=({ff["SWx"]},{ff["SWy"]},0);ne=({ff["SWx"] + ff["Lx"]},{ff["SWy"] + ff["Ly"]},0);t=0]'
ff.execute(domain_string)

# Add the required Forefire layers
# ff.addLayer("BRatio","BRatio","BRatio")  ## Time of arrival matrix 
ff.addLayer("propagation",ff["propagationModel"],"propagationModel")  ## Propagation model 
# ff.addLayer("propagation","ANNPropagationModel","propagationModel")

ff.addLayer("data","windU","windU")
ff.addLayer("data","windV","windV") #wind layers
ff.addIndexLayer("table", "fuel", float(ff["SWx"]), float(ff["SWy"]), 0, domain_width, domain_height, 0, fuel_map) ## Fuel map layer

##  front orentation is clockwise!!
ff.execute(f"\tFireFront[id=2;domain=0;t=0]")
ff.execute(f"\t\tFireNode[domain=0;loc=({xp1},{yp1},0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute(f"\t\tFireNode[domain=0;loc=({xp2},{yp2},0);vel=(0,0,0);t=0;state=init;frontId=2]")
ff.execute(f"\t\tFireNode[domain=0;loc=({xp3},{yp3},0);vel=(0,0,0);t=0;state=init;frontId=2]")
# ff.execute("startFire[loc=(xp1,xp2,0);t=0]")

# Loop over number of timesteps, step by step_size
pathes = []
bournawt=[]
times=[]
for i in range(1, nb_steps+1):
    try:
        # Advance timestep by step_size
        print("goTo[t=%f]" % (i*step_size))
        ff.execute("goTo[t=%f]" % (i*step_size))
        # Get pathes from previous execution
        newPathes = printToPathe(ff.execute("print[]"))
        pathes += newPathes
        bmap=ff.getDoubleArray("BMap")
        burnrbool = np.logical_not(np.isinf(bmap))
        # Count the True values in non_inf array
        burnr = np.sum(burnrbool*np.power(float(ff["minimalPropagativeFrontDepth"]),2))
        bournawt.append(burnr)
        times.append(i*step_size)


    except KeyboardInterrupt:
        # Keyboard interrupt in case simulation take a while and we want to show current state of simulation
        break
##-----------------------------------------------------------------------------
##  SIMULATION ENDS
##-----------------------------------------------------------------------------  
    
##-----------------------------------------------------------------------------
##   Plot the simulated Fronts
##-----------------------------------------------------------------------------
ffplotExtents =(float(ff["SWx"]),float(ff["SWx"]) + float(ff["Lx"]),float(ff["SWy"]),float(ff["SWy"]) + float(ff["Ly"]))
plot_test(pathes,fuel_map)
