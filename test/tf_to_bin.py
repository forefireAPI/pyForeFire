import sys
import os
import tensorflow as tf
from forefire_TF_helpers import save_model_structure, load_model_structure
import pdb


tf_model_path = sys.argv[1]
bin_model_path = os.path.join(tf_model_path, 'saved_model.ffann')

if not os.path.exists(bin_model_path):
    model = tf.keras.saving.load_model(tf_model_path)
    save_model_structure(
        model, 
        bin_model_path, 
        input_names=[
            "normalWind", 
            "slope", 
            "fuel.Md", 
            "fuel.DeltaH", 
            "fuel.DeltaH", 
            "fuel.DeltaH",
            "fuel.DeltaH",
            "fuel.DeltaH",
            "fuel.DeltaH"
            ], 
        output_names=['ROSx']
        )
    # ['wind', 'slope', 'mdOnDry1h', 'H', 'SAVcar', 'fd', 'fuelDens', 'Dme', 'fl1h']

model, input_names, output_names = load_model_structure(bin_model_path)