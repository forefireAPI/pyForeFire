import numpy as np
import tensorflow as tf
import time
import struct

def save_model_structure(model, filename, input_names=None, output_names=None):
    with open(filename, 'wb') as file:
        # Header
        header_format = '8s i'
        nlayers = 0

        for layer in model.layers:
            if len(layer.get_weights() ) == 2:
                nlayers = nlayers+1
        file.write(struct.pack(header_format, b'FFANN001', nlayers))
        
        for layer in model.layers:
            # Check if the layer has weights
            weights_biases = layer.get_weights()
            if len(weights_biases) == 2:
                weights, biases = weights_biases
                weights_shape = weights.shape
                biases_shape = biases.shape
                activation = layer.get_config().get('activation', 'NONE')
             
                # Map activation functions to codes
                activation_code = {
                    'relu': b'RELU',
                    'sigmoid': b'SIGM',
                    'linear': b'LINE'
                }.get(activation, b'NONE')

                # Layer details
                layer_format = '4s ii'
                file.write(struct.pack(layer_format, activation_code, weights_shape[0], weights_shape[1]))

                # Save weights and biases in float32 format
                weights_format = f'{weights.size}f'
                biases_format = f'{biases.size}f'
                file.write(struct.pack(weights_format, *weights.flatten()))
                file.write(struct.pack(biases_format, *biases.flatten()))
            else:
                # Handle layers without weights and biases
                activation_code = b'NONE'
                layer_format = '4s ii'
                print("problem")
                # Save input and output names at the end of the file
        # Convert input and output names to byte arrays or use empty bytes if None
        # Names and their lengths
        input_names_bytes = ','.join(input_names).encode() if input_names else b''
        output_names_bytes = ','.join(output_names).encode() if output_names else b''
        file.write(struct.pack('i', len(input_names_bytes)))
        file.write(input_names_bytes)
        file.write(struct.pack('i', len(output_names_bytes)))
        file.write(output_names_bytes)


                #file.write(struct.pack(layer_format, activation_code, 0, 0))


# Define the dataset

inputs = np.array([[1, 0, 0, 0, 0],
                   [0, 0, 0, 0, 0],
                   [2, 0, 0, 0, 0],
                   [0, 0, 0, 0, 0],
                   [0, 0, 0, 0, 0]], dtype=np.float32)
outputs = np.array([[0], [0.1], [0.0], [0.1], [0.1]], dtype=np.float32)

# Create a sequential model with dropout layers
model = tf.keras.Sequential([
    # Input layer
    tf.keras.layers.Dense(4, input_shape=(5,), activation='sigmoid'),
 #   tf.keras.layers.Dropout(0.2),  # Dropout 20% of the nodes in the first hidden layer during training
    
#    tf.keras.layers.Dense(512, activation='sigmoid'),
    # Second layer
    tf.keras.layers.Dense(4, activation='sigmoid'),
    
    # Output layer
    tf.keras.layers.Dense(1, activation='linear', name='output')
])
# Compile the model
model.compile(optimizer='adam', loss='mean_squared_error')

# Train the model
model.fit(inputs, outputs, epochs=500)

save_model_structure(model, 'mbase.ffann',input_names=["slope","normalWind","fuel.Rhod","fuel.sd","fuel.Ta"], output_names=["ROSx"])
# Generate 100000 random inputs
all_input = np.random.rand(100000, 5).astype(np.float32)

# Measure inference time for 100,000 inputs
start_time = time.time()
predicted_output = model.predict(all_input)
end_time = time.time()

print(f"Time taken for predicting 100,000 inputs: {end_time - start_time} seconds")

# Verification inputs
verification_inputs = np.array([
    [1, 1, 1, 0, 0],
    [1, 0, 0, 0, 0],
    [0, 1, 0, 0, 0],
    [0, 0, 1, 0, 0],
    [0, 0, 0, 1, 0],
    [0, 0, 0, 0, 1],
    [0, 1, 0, 1, 0]
], dtype=np.float32)

# Predict using the verification inputs
verification_output = model.predict(verification_inputs)

# Print results for verification inputs
verification_results = ["[1 1 1 0 0]", "[1 0 0 0 0]", "[0 1 0 0 0]", "[0 0 1 0 0]",
                        "[0 0 0 1 0]", "[0 0 0 0 1]", "[0 1 0 1 0]"]
for i, result in enumerate(verification_output):
    print(f"{verification_results[i]} result: {result[0]}")
