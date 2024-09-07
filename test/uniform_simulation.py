from forefire_helper import *
from simulation import UniformForeFireSimulation
import argparse
import yaml


def uniform_simulation(config):
    propagation_model = config['propagation_model']

    if 'fuels_table' in config:
        fuels_table = fuels_table
    else:
        fuels_table = get_fuels_table(propagation_model)
    fuel_type = config['fuel_type']
    domain_width = config['domain_width']
    domain_height = config['domain_height']
    domain = (0, 0, domain_width, domain_height)
    horizontal_wind = config['horizontal_wind']
    vertical_wind = config['vertical_wind']
    slope = config['slope']
    fire_front = config['fire_front']
    spatial_increment = config['spatial_increment']
    minimal_propagative_front_depth = config['minimal_propagative_front_depth']
    perimeter_resolution = config['perimeter_resolution']
    relax = config['relax']
    smoothing = config['smoothing']
    min_speed = config['min_speed']
    burned_map_layer = config['burned_map_layer']

    simulation = UniformForeFireSimulation(
        propagation_model,
        domain,
        fuels_table,
        horizontal_wind,
        vertical_wind,
        fuel_type,
        slope,
        fire_front,
        spatial_increment,
        minimal_propagative_front_depth,
        perimeter_resolution,
        relax,
        smoothing,
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

    uniform_simulation(config)