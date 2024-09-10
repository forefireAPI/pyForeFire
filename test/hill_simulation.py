from forefire_helper import *
from simulation import UniformWindForeFireSimulation
import argparse
import yaml
import numpy as np
import matplotlib.pyplot as plt
import pdb


def hill(x, mean, cov, height=100):
    N = len(mean)
    den = (2*np.pi)**(N/2) * np.linalg.det(cov)**0.5
    exp = np.exp(-0.5 * np.einsum('...k,kl,...l->...', x-mean, np.linalg.inv(cov), x-mean))
    gaussian = exp / den
    altitude = height * (gaussian - gaussian.min()) / (gaussian.max() - gaussian.min())
    return altitude


def hill_simulation(config):
    propagation_model = config['propagation_model']
    nn_ros_model_path = config['nn_ros_model_path']

    if 'fuels_table' in config:
        fuels_table = fuels_table
    else:
        fuels_table = get_fuels_table(propagation_model)
    fuel_type = config['fuel_type']
    domain_width = config['domain_width']
    domain_height = config['domain_height']
    domain = (0, 0, domain_width, domain_height)

    # Create hill with a 2D gaussian
    mean = np.array([domain_height // 2, domain_width //2])
    cov = np.array([
        [1e5, 0],
        [0, 1e5]])

    map_x, map_y = np.meshgrid(
        np.arange(domain_height),
        np.arange(domain_width)
    )

    map = np.empty(map_x.shape + (2,))
    map[:, :, 0] = map_x
    map[:, :, 1] = map_y

    altitude_map = hill(map, mean, cov) 
    # plt.imshow(altitude_map); plt.show()  

    fuel_map = np.ones_like(altitude_map)
    fuel_map[:, :domain_width // 2] = fuel_type[0]
    fuel_map[:, :domain_width // 2] = fuel_type[1]
    
    horizontal_wind = config['horizontal_wind']
    vertical_wind = config['vertical_wind']

    fire_front = config['fire_front']
    spatial_increment = config['spatial_increment']
    minimal_propagative_front_depth = config['minimal_propagative_front_depth']
    perimeter_resolution = config['perimeter_resolution']
    relax = config['relax']
    min_speed = config['min_speed']
    burned_map_layer = config['burned_map_layer']

    simulation = UniformWindForeFireSimulation(
        propagation_model,
        fuels_table,
        horizontal_wind,
        vertical_wind,
        fuel_map,
        altitude_map,
        fire_front,
        nn_ros_model_path,
        spatial_increment,
        minimal_propagative_front_depth,
        perimeter_resolution,
        relax,
        min_speed,
        burned_map_layer,
    )

    nb_steps = config['nb_steps']
    step_size = config['step_size']

    # Run simulation
    pathes = simulation(nb_steps, step_size)

    ##-----------------------------------------------------------------------------
    ##   Plot the simulated Fronts
    ##-----------------------------------------------------------------------------
    plotExtents = (
        float(simulation.ff["SWx"]),
        float(simulation.ff["SWx"]) + float(simulation.ff["Lx"]),
        float(simulation.ff["SWy"]),
        float(simulation.ff["SWy"]) + float(simulation.ff["Ly"]))
    plot_simulation(pathes, simulation.fuel_map[0, 0], simulation.altitude_map[0, 0], plotExtents, None)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, 
                        help='Path to the config file (.yaml) of the simulation.')
    parser.add_argument('--propagation_model', type=str, default='RothermelAndrews2018', 
                        help='Rate of Spread model (default: RothermelAndrews2018)')
    parser.add_argument('--fuel_type', type=int, default=6,
                        help='Index of the fuel type to use (default: 6)')
    parser.add_argument('--domain_width', type=int)
    parser.add_argument('--domain_height', type=int)
    parser.add_argument('--horizontal_wind', type=float)
    parser.add_argument('--vertical_wind', type=float)
    parser.add_argument('--slope', type=float)
    parser.add_argument('--nb_steps', type=int,
                        help='Number of simulation steps')
    parser.add_argument('--step_size', type=float,
                        help='Duration (in seconds) between each step.')
    args = parser.parse_args()

    if args.config:
        with open(args.config, 'r') as stream:
            config = yaml.safe_load(stream)
    else:
        config = vars(args)

    hill_simulation(config)