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
import pandas as pd

import tensorflow as tf
from forefire_helper import *
from forefire_TF_helpers import *

# All you need to do a propagation model / simulation emulation
# Keep in mind the emulator will be somehow linked to the numerical model in use
# you have to run this script 3 times for the 3 phases, each time go to next phase


phaseRunForANN = 1
#1 make a sample run with a model to generate Atime matrix, this is a simulation to create some kind of data to learn from
#2 extract the model keys andcreate an empty FFANN with the same inputs found as keys

phaseMakeDBandRun = 2
#3 run with the same but in mode forced.. so it generates a database of ros vs values to be used in midel fit
#4 use the data to fir the network weights

phaseUseANNROSandCompare = 3
#5 use the just fitted annModel to make simulation 
#6 compare original simulations with the first run

# SET THE PHASE HERE runwith 1, then 2, then 3
phase = phaseUseANNROSandCompare

print(f"Hello !! making some fire model emulation\n Running phase {phase} over 3")


landscape_file_path = "sampleUVCoeffLandscape.nc"
at_file_path = "ForeFire.0.nc"
initialPropagationModel = "Rothermel"

ff = forefire.ForeFire()
ff["fuelsTable"] = standardRothermelFuelTable()
ff["spatialIncrement"] = 3
ff["perimeterResolution"] = 10
ff["minimalPropagativeFrontDepth"] = 40
ff["minSpeed"] = 0.0
ff["relax"] = 1
ff["propagationSpeedAdjustmentFactor"] = 1
ff["windReductionFactor"]=1
ff["bmapLayer"] = 1


ff["FFANNPropagationModelPath"] = f"{initialPropagationModel}.ffann"
ff["FFBMapLoggerCSVPath"] = f"{initialPropagationModel}db.csv"
ff["LookAheadDistanceForeTimeGradientDataLayer"] = 40   


if phase == phaseRunForANN:
    ff["propagationModel"] = initialPropagationModel
    
if phase == phaseMakeDBandRun:
    ff["propagationModel"] = "BMapLoggerForANNTraining"
    
if phase == phaseUseANNROSandCompare:
    ff["propagationModel"] = "ANNPropagationModel"
    

ff.execute(f'loadData[{landscape_file_path};2009-07-24T11:37:39Z]')
print("loaded data at ",float(ff["SWx"]), float(ff["SWy"]), "size", float(ff["Lx"]), "X",float(ff["Ly"]))

if phase == phaseMakeDBandRun:
    lcp = xr.open_dataset(at_file_path)
    at_map = np.expand_dims(np.expand_dims(lcp.arrival_time_of_front.data, axis=0), axis=0)
    at_map[at_map <=0] = 0
    lcp.close()
    ff.addScalarLayer("data", "forced_arrival_time_of_front", float(ff["SWx"]), float(ff["SWy"]), 0, float(ff["Lx"]), float(ff["Ly"]), 0, at_map) 
    
ff.execute("startFire[loc=(506666,4625385,0);t=0]")
ff.execute("startFire[loc=(506666,4614485,0);t=0]")
ff.execute("startFire[loc=(480666,4615385,0);t=0]")
start_time = time.time()

pathes = []

nb_steps = 5  # The number of steps the simulation will execute
step_size = 360  # The duration (in seconds) between each step
angle_deg = 30.0  # The angle by which to rotate the vector at each step
norm = 20  # The norm of the vector

for i in range(nb_steps):
    rotation_angle_rad = math.radians(i * angle_deg)
    herex = norm * math.cos(rotation_angle_rad)
    herey = norm * math.sin(rotation_angle_rad)
    angle_deg = angle_deg-(0.5)
    try:
        new_out = ff.execute("print[]")
        newPathes = printToPathe(new_out)
        ff.execute(f"trigger[wind;loc=(0.,0.,0.);vel=({herex},{herey},0);t=0.]")
        ff.execute("step[dt=%f]" % (step_size))
        print(f"Simulation step {i}/{nb_steps} t:{i*step_size}")
        pathes += newPathes
        
    except KeyboardInterrupt:
        break

end_time = time.time()
duration = end_time - start_time
print(f"Total time taken for simulation : {duration} seconds")

at=None

if phase == phaseRunForANN:
    ff.execute("save[]")
    input_names=ff[initialPropagationModel+".keys"].split(";")
    input_size = len(input_names)
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(32, input_shape=(len(input_names),), activation='relu'),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(1, activation='linear', name='output')
    ])
    save_model_structure(model, ff["FFANNPropagationModelPath"], input_names=input_names, output_names=["ROS"])
    at=ff.getDoubleArray("BMap")[0,0,:,:]
else:
    lcp = xr.open_dataset(at_file_path)   
    at=lcp.arrival_time_of_front.data
    lcp.close
    
    
if phase == phaseMakeDBandRun:
    model, input_names, output_names = load_model_structure(ff["FFANNPropagationModelPath"])
    
    data = pd.read_csv(ff["FFBMapLoggerCSVPath"] , delimiter=';')  # Adjust delimiter if necessary
    
    
    filtered_data = data[(data['ROS'] < 1) & (data['normalWind'] > -1)]

    #Sort data by 'ROS'
    sorted_data = filtered_data.sort_values(by='ROS')
    
    # Plotting
    plt.figure(figsize=(14, 7))
    
    # Plot 'ROS' vs 'normalWind'
    plt.subplot(1, 2, 1)  # 1 row, 2 columns, first plot
    plt.scatter(sorted_data['ROS'], sorted_data['normalWind'], color='blue')
    plt.title('ROS vs normalWind')
    plt.xlabel('ROS')
    plt.ylabel('normalWind')
    
    # Plot 'ROS' vs 'slope'
    plt.subplot(1, 2, 2)  # 1 row, 2 columns, second plot
    plt.scatter(sorted_data['ROS'], sorted_data['slope'], color='green')
    plt.title('ROS vs Slope')
    plt.xlabel('ROS')
    plt.ylabel('Slope')
    
    # Show plot
    plt.tight_layout()
    plt.show()
    
    
    inputs = filtered_data[input_names]
    outputs = filtered_data[output_names]
    
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(inputs.to_numpy(), outputs.to_numpy(), epochs=50)
    
    save_model_structure(model, ff["FFANNPropagationModelPath"], input_names=input_names, output_names=["ROS"])
    

    
ffplotExtents =(float(ff["SWx"]),float(ff["SWx"]) + float(ff["Lx"]),float(ff["SWy"]),float(ff["SWy"]) + float(ff["Ly"]))   
plot_simulation(pathes,None ,None,  ffplotExtents,scalMap=at) 
    