import sys
import os
import tensorflow as tf
from forefire_TF_helpers import save_model_structure, load_model_structure
import pdb


tf_model_path = sys.argv[1]
bin_model_path = os.path.join(tf_model_path, 'saved_model.ffann')

if not os.path.exists(bin_model_path):
    model = tf.keras.saving.load_model(tf_model_path)
    import pdb; pdb.set_trace()
    save_model_structure(
        model, 
        bin_model_path, 
        input_names=[
            "normalWind", # Normal wind
            "slope", # Slope
            "fuel.Md", # Fuel particle moisture content
            "fuel.DeltaH", # Fuel particle low heat content
            "fuel.sd", # Fuel Particle surface area to volume ratio (1/ft)
            "fuel.e", # Fuel depth (ft)
            "fuel.Rhod", # Ovendry particle density
            "fuel.me", # Moisture content of extinction
            "fuel.Sigmad" # Ovendry fuel loading 
            ], 
        output_names=['ROSx']
        )
    # ['wind', 'slope', 'mdOnDry1h', 'H', 'SAVcar', 'fd', 'fuelDens', 'Dme', 'fl1h']

model, input_names, output_names = load_model_structure(bin_model_path)