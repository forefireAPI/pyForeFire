import numpy as np
import tensorflow as tf
import time
import struct
from pyforefire.helpers import *
from wildfire_ROS_models.tf_ros_model import *

def emptyModelForLog(input_names,ANN_output_path):
    input_size = len(input_names)
#    inputs = np.ones((5,input_size), dtype=np.float32)
#    outputs = np.ones((5,1), dtype=np.float32)
    
    model = tf.keras.Sequential([
        # Input layer
        tf.keras.layers.Dense(4, input_shape=(input_size,), activation='sigmoid'),
        tf.keras.layers.Dense(16, activation='sigmoid'),
        tf.keras.layers.Dense(1, activation='linear', name='output')
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')  
  #  model.fit(inputs, outputs, epochs=1)
    save_model_structure(model, ANN_output_path, input_names=input_names, output_names=["ROS"])
        
        
def sampleRun():
    inputs = np.array([[1, 0, 0.1, 0, 0.2],
                       [0, 1, 0, 0.2, 0],
                       [2, 2, 0, 0.1, 0],
                       [0, 3, 0.1, 0, 0],
                       [0, 4, 0, 0, 0]], dtype=np.float32)
    outputs = np.array([[0], [0.1], [0.2], [0.3], [0.4]], dtype=np.float32)

    model = tf.keras.Sequential([
        # Input layer
        tf.keras.layers.Dense(4, input_shape=(5,), activation='sigmoid'),
        tf.keras.layers.Dense(4, activation='sigmoid'),
        tf.keras.layers.Dense(1, activation='linear', name='output')
    ])
    # Compile the model
    model.compile(optimizer='adam', loss='mean_squared_error')
    
    model.fit(inputs, outputs, epochs=500)
    
    save_model_structure(model, 'mbase.ffann',input_names=["slope","normalWind","fuel.Rhod","fuel.sd","fuel.Ta"], output_names=["ROSx"])
    all_input = np.random.rand(100000, 5).astype(np.float32)
    
    start_time = time.time()
    predicted_output = model.predict(all_input)
    end_time = time.time()
    
    print(f"Time taken for predicting 100,000 inputs: {end_time - start_time} seconds")
    
    # Verification inputs
    verification_inputs = np.array([
        [1, 1, 1, 0, 0],
        [1, 0, 0, 0, 0],
        [0, 2, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 4, 0, 1, 0],
        [0, 1, 0, 0, 1],
        [0, 1, 0, 1, 0]
    ], dtype=np.float32)
    
    # Predict using the verification inputs
    verification_output = model.predict(verification_inputs)
    
    # Print results for verification inputs
 
    for i, result in enumerate(verification_output):
        print(f"{verification_inputs[i]} result: {result[0]}")
        
emptyModelForLog(["fuel.vv_coeff",],"empty.ffann")
sampleRun()