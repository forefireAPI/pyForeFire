#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 17:09:33 2024

@author: baggio_r2
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import pyforefire as pyff


###############################################################################
##:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#                    IDEALIZED TEST CASE UNSTEADY
##::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: 
## Steady vs unsteady front behaviour when encountering an obstacle are compared
## Fire relevant example: Propagating fire encounters a water barrier 
##-----------------------------------------------------------------------------
## Propagation model "UnsteadyPropagation"-> 
##      ROS=windReductionFactor*valueOf[normalWind]*speed_module*lvv_coeff*(1+lfdepth/(1+lfdepth));
## History of fire peopagation is taking into account trough the param fdepth (front depth)
##-----------------------------------------------------------------------------
## The depth of the front is evaluated by means of an HeatFluxModel, in this example
##
## FluxModel--> HeatFluxBasicFuel:
##* Mean heat flux released between the time interval [bt, et] */
##	/* The heat flux is supposed to be constant from the arrival time (at)
##	 * and for a period of time of 'burningDuration', constant of the model */
##      - burningDuration=valueOf[BD_coeff]*burningDuration;
##      - nominalHeatFlux=valueOf[HF_coeff]*nominalHeatFlux;
##-----------------------------------------------------------------------------
##
## - change the constant propagation velocity by setting: 
##      ff["speed_module"]=value
## - change coefficients vv_coeff,BD_coeff,HF_coeff by editing "VVCoeffTable()"
##
## To simulate inhomogeneous propagation:
##     1) add rows to the fuel table VVCoeffTable():

##    |Index|vv_coeff|BD_coeff|HF_coeff|
##    |-----|--------|--------|--------|
##    |1    |1.0     | 1.0    | 1.0    |
##    |-----|--------|--------|--------|
##    |2    |1.0     | 0.1    | 1.     |   
##    |-----|--------|--------|--------|
##      ...    ...     ...  ...
##
##
##     2) edit the fuelmap using a pattern of "Index" values
##     Ex:
##         fuel_map[:,:,:,:int(.5*sim_shape[1])].fill(valueofIndex1)    
##         fuel_map[:,:,:,int(.5*sim_shape[1]):].fill(valueofIndex2)
###############################################################################

##-----------------------------------------------------------------------------
##  Fuel type table
def VVCoeffTable():
    return """Index;vv_coeff;Kdepth;BD_coeff;HF_coeff
1;1.0;0.1;50.0;10.0
2;1.0;0.0;0.0;0.0
3;0.0;0.0;0.0;0.0"""

##-----------------------------------------------------------------------------
##  Simulation parameters and settings ##
##-----------------------------------------------------------------------------
## 
nb_steps = 20  #200             # The number of step the simulation will execute
step_size = 3 #1               # The duration (in seconds) of time steps
fuel_type = 1                   # The type of used fuel by default (Index in VVCoeffTable() )

##   Initialize pyforefire module
ff = pyff.ForeFire()

##  Fuel settings
ff["fuelsTable"] = VVCoeffTable()
ff["defaultFuelType"]=1.
##  ForeFire settings
ff["spatialIncrement"]=0.2
ff["minimalPropagativeFrontDepth"]=0.0
ff["perimeterResolution"]=5
ff["initialFrontDepth"]=1
ff["initialBurningDuration"]=30
ff["relax"]=1
ff["smoothing"]=100
ff["minSpeed"]=0.0
ff["bmapLayer"]=1
## Constant wind speed
ff["windU"]=1.0 # Horizontal
ff["windV"]=0.0 # Vertical
##  Propagation model settings
##############################
ff["frontDepthComputation"]=1
#############################
ff["windReductionFactor"]=1. 
ff["speed_module"]=1.  ## spreading velocity (meters seconds-1)
ff["propagationModel"] = "FrontDepthDriven"#"FrontDepthDriven"##"IsotropicFuel"
## HeatFlux Model Setting:
ff["FluxModel"]="heatFluxBasic"
ff["defaultHeatType"]=0
ff["nominalHeatFlux"]=100000
ff["burningDuration"]=float(ff["initialBurningDuration"])
    
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
band_start = 700 # X coordinate 
band_depth = 3 #integer, dimension of thee propagation barrier
fuel_map = np.zeros((1, 1) + sim_shape)
fuel_map.fill(fuel_type)
# fuel_map[:,:,int(.5*sim_shape[0]):,:].fill(2)   
fuel_map[:,:,:,band_start:band_start+band_depth].fill(3)   
# plt.imshow(fuel_map[0,0,:,:])
##-----------------------------------------------------------------------------
##  SIMULATION STARTS
##-----------------------------------------------------------------------------    
domain_string = f'FireDomain[sw=({ff["SWx"]},{ff["SWy"]},0);ne=({ff["SWx"] + ff["Lx"]},{ff["SWy"] + ff["Ly"]},0);t=0]'
ff.execute(domain_string)

## Add the required Forefire layers
ff.addLayer("BRatio","BRatio","BRatio")  ## Time of arrival matrix 
ff.addLayer("propagation",ff["propagationModel"],"propagationModel") ## Propagation model
ff.addLayer("flux",ff["FluxModel"],"defaultHeatType") ## HeatFlux  model
ff.addLayer("data","windU","windU")
ff.addLayer("data","windV","windV") #wind layers
ff.addIndexLayer("table", "fuel", float(ff["SWx"]), float(ff["SWy"]), 0, domain_width, domain_height, 0, fuel_map) ## Fuel map layer

## "Ignition" points
# pointxcenter=domain_width//2
# pointycenter=domain_height//2
# xp1=pointxcenter
# yp1=pointycenter
xp1=domain_width//4
yp1=domain_height//2-domain_height//4
xp2=domain_width//4
yp2=domain_height//2+domain_height//4
# ff.execute(f"startFire[loc=({xp1},{yp1},0.);t=0.0];frontId=4]")
# ff.execute(f"startFire[loc=({xp2},{yp2},0.);t=0.0,;frontId=3]")
sidey=500
sidex=100
xdiff=0

timesq=0.

xsq1,ysq1=domain_width//8+sidex,domain_height//8
xsq2,ysq2=domain_width//8,domain_height//8
xsq3,ysq3=domain_width//8,domain_height//8+sidey
xsq4,ysq4=domain_width//8+sidex,domain_height//8+sidey

x2sq1,y2sq1=domain_width//8+sidex,5*domain_height//8
x2sq2,y2sq2=domain_width//8,5*domain_height//8
x2sq3,y2sq3=domain_width//8,5*domain_height//8+sidey
x2sq4,y2sq4=domain_width//8+sidex,5*domain_height//8+sidey

ff.execute(f"\tFireFront[id=2;domain=0;t=0]")
ff.execute(f"\t\tFireNode[domain=0;loc=({xsq1},{ysq1},0);vel=(0,0,0);t={timesq};state=init;frontId=2]")
ff.execute(f"\t\tFireNode[domain=0;loc=({xsq2},{ysq2},0);vel=(0,0,0);t={timesq};state=init;frontId=2]")
ff.execute(f"\t\tFireNode[domain=0;loc=({xsq3},{ysq3},0);vel=(0,0,0);t={timesq};state=init;frontId=2]")
ff.execute(f"\t\tFireNode[domain=0;loc=({xsq4},{ysq4},0);vel=(0,0,0);t={timesq};state=init;frontId=2]")

ff.execute(f"\tFireFront[id=3;domain=0;t=0]")
ff.execute(f"\t\tFireNode[domain=0;loc=({x2sq1+xdiff},{y2sq1},0);vel=(0,0,0);t={timesq};state=init;frontId=3]")
ff.execute(f"\t\tFireNode[domain=0;loc=({x2sq2+xdiff},{y2sq2},0);vel=(0,0,0);t={timesq};state=init;frontId=3]")
ff.execute(f"\t\tFireNode[domain=0;loc=({x2sq3+xdiff},{y2sq3},0);vel=(0,0,0);t={timesq};state=init;frontId=3]")
ff.execute(f"\t\tFireNode[domain=0;loc=({x2sq4+xdiff},{y2sq4},0);vel=(0,0,0);t={timesq};state=init;frontId=3]")
# 
# Loop over number of timesteps, step by step_size
pathes = [] ##list to store fronts
bournawt=[] ##list to store spanned area
times=[]
errort=[]   ##list to store relative error with time 
##-----------------------------------------------------------------------------
##  declare the implied v_coeff for surface check (only for homogeneous spreading!)
v_coeff=1.
##-----------------------------------------------------------------------------
for i in range(1, nb_steps+1):
    try:
        # Advance timestep by step_size
        
        ff.execute("goTo[t=%f]" % (i*step_size))
        fdepth=ff['frontDepth']
        print(f"goTo[t={(i*step_size)}]") 
        # Get pathes from previous execution
        newPathes = pyff.helpers.printToPathe(ff.execute("print[]"))
        pathes += newPathes
        bmap=ff.getDoubleArray("BMap")
        hey=ff.getDoubleArray('frontDepth')
        # print(f"ff.getDoubleArray('frontDepth'): {hey}")
        # print(f" frontDepth: {ff['frontDepth']} newFrontDepth: {ff['newFrontDepth']}")
        # print(ff.getDouble("heatFlux.activeArea"),ff.getDoubleArray("heatFlux"))
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
##  
##-----------------------------------------------------------------------------
##   Plot the simulated Fronts
##-----------------------------------------------------------------------------
# velcof=float(ff["speed_module"])
# x1=pointxcenter-velcof*float(ff["speed_module"])*nb_steps*step_size
# y1=x1
# x2=pointxcenter+velcof*float(ff["speed_module"])*nb_steps*step_size
# y2=x2
# fact=0.2
# ffplotExtents=(x1-fact*domain_width,x2+fact*domain_width,y1-fact*domain_height,y2+fact*domain_height)
# plot_simulation(pathes,None ,None,  ffplotExtents ,scalMap=None)
ffplotExtents =(float(ff["SWx"]),float(ff["SWx"]) + float(ff["Lx"]),float(ff["SWy"]),float(ff["SWy"]) + float(ff["Ly"]))
pyff.helpers.plot_simulation(pathes,None ,None,  ffplotExtents ,scalMap=ff.getDoubleArray("BMap")[0,0,:,:])