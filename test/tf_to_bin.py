import sys
import os
import tensorflow as tf
from forefire_TF_helpers import save_model_structure, load_model_structure
import pdb


tf_model_path = sys.argv[1]
bin_model_path = os.path.join(tf_model_path, 'saved_model.ffann')

rothermel_andrews_2018_input_names = [
    "fuel.fl1h_tac",
    "fuel.fd_ft",
    "fuel.Dme_pc",
    "fuel.SAVcar_ftinv",
    "fuel.H_BTUlb",
    "fuel.totMineral_r",
    "fuel.effectMineral_r",
    "fuel.fuelDens_lbft3",
    "fuel.mdOnDry1h_r",
    "normalWind",
    "slope"
    ]

if not os.path.exists(bin_model_path):
    model = tf.keras.saving.load_model(tf_model_path)
    save_model_structure(
        model, 
        bin_model_path, 
        input_names=rothermel_andrews_2018_input_names,
        output_names=['ROSx']
        )

model, input_names, output_names = load_model_structure(bin_model_path)