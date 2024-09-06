from forefire_helper import *
from simulation import UniformForeFireSimulation
import argparse
import yaml


def run_simulation(config):
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
    vertical_wind = config['horizontal_wind']

    slope = config['slope'] #TODO : add uniform slope

    # TODO: add config start fire
    pointxcenter = domain_width // 2
    pointycenter = domain_height // 2
    h1, w1 = 50, 50
    xp1,yp1 = pointxcenter, pointycenter + h1
    xp2,yp2 = pointxcenter + w1, pointycenter
    xp3,yp3 = pointxcenter - w1, pointycenter
    fire_front = ((xp1, yp1), (xp2, yp2), (xp3, yp3))

    simulation = UniformForeFireSimulation(
        propagation_model,
        domain,
        fuels_table,
        horizontal_wind,
        vertical_wind,
        fuel_type,
        slope,
        fire_front
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
    plot_simulation(pathes, simulation.fuel_map[0, 0], None, plotExtents, None)
    # plot_test(pathes,simulation.fuel_map)


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

    run_simulation(config)