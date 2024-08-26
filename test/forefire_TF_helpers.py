import struct
import numpy as np
import tensorflow as tf

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



def load_model_structure(filename):
    with open(filename, 'rb') as file:
        # Read and unpack the header
        header_format = '8s i'
        header_size = struct.calcsize(header_format)
        header = file.read(header_size)
        _, nlayers = struct.unpack(header_format, header)

        # Prepare to reconstruct the model
        model = tf.keras.Sequential()
        
        # Read and reconstruct each layer
        layer_format = '4s ii'
        for _ in range(nlayers):
            layer_info = file.read(struct.calcsize(layer_format))
            activation_code, num_inputs, num_outputs = struct.unpack(layer_format, layer_info)

            # Convert byte-encoded activation function to string
            activation = {
                b'RELU': 'relu',
                b'SIGM': 'sigmoid',
                b'LINE': 'linear',
                b'NONE': None  # Default or error handling case
            }.get(activation_code, 'linear')  # Default to linear if unknown code

            # Read weights
            weights_size = num_inputs * num_outputs
            weights_format = f'{weights_size}f'
            weights = np.array(struct.unpack(weights_format, file.read(weights_size * 4)), dtype=np.float32).reshape((num_inputs, num_outputs))

            # Read biases
            biases_format = f'{num_outputs}f'
            biases = np.array(struct.unpack(biases_format, file.read(num_outputs * 4)), dtype=np.float32)

            # Create layer with weights and activation
            layer = tf.keras.layers.Dense(num_outputs, activation=activation, input_shape=(num_inputs,))
            model.add(layer)
            # Set weights manually
            layer.set_weights([weights, biases])

        # Read input and output names
        input_names_len = struct.unpack('i', file.read(4))[0]
        input_names_bytes = file.read(input_names_len)
        input_names = input_names_bytes.decode().split(',') if input_names_bytes else []

        output_names_len = struct.unpack('i', file.read(4))[0]
        output_names_bytes = file.read(output_names_len)
        output_names = output_names_bytes.decode().split(',') if output_names_bytes else []

        return model, input_names, output_names
