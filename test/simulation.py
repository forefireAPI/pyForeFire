import sys
import logging
from typing import Optional, Tuple, List

import numpy as np

import pyforefire as forefire
from forefire_helper import *


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger()

class ForeFireSimulation:
    """
    Generic class for a ForeFire simulation.
    """
    def __init__(
            self, 
            propagation_model: str,
            domain: Tuple[int],
            fuels_table: callable,
            spatial_increment: Optional[float] = None,
            minimal_propagative_front_depth: Optional[float] = None,
            perimeter_resolution: Optional[float] = None,
            relax: Optional[float] = None,
            min_speed: Optional[float] = None,
            burned_map_layer: Optional[int] = None,
            ):
        """
        Initialize the ForeFire simulation.
        Args:
            propagation_model (str): name of the Rate of Spread model (e.g. Rothermel, RothermelAndrews2018).
            domain (tuple): (SWx, SWy, Lx, Ly) where (SWx, SWy) are the coordinates of the top-left corner 
            of the domain, Lx is the domain width and Ly is the domain height.
            fuels_table (callable): a callable reading a fuels table 
            (e.g. RothermelAndrews2018FuelTable from src/forefire_helper.py)
            spatial_increment (float): distance (in meters) between new and old node position
            minimal_propagative_front_depth (float): resolution (in meters) of the arrival time matrix
            perimiter_resolution (float): maximal distance (in meters) between two nodes
            relax (float): weights the new and old ROS (ROS = relax x new_ROS + (1 - relax) x old_ROS)
            min_speed (float): minimal speed (m/s), i.e. ROS = max(ROS, min_speed)
            max_speed (float): maximal speed (m/S), i.e. ROS = min(ROS, max_speed)
        """
        # Initialize pyforefire module
        ff = forefire.ForeFire()
        ff["propagationModel"] = propagation_model
        ff["SWx"], ff["SWy"], ff["Lx"], ff["Ly"] = domain
        ff["fuelsTable"] = fuels_table()

        if spatial_increment:
            assert spatial_increment > 0, 'spatial_increment must be strictly positive'
            ff["spatialIncrement"] = spatial_increment
        if minimal_propagative_front_depth:
            assert minimal_propagative_front_depth > 0, 'minimal_propagative_front_depth must be strictly positive'
            ff["minimalPropagativeFrontDepth"] = minimal_propagative_front_depth
        if perimeter_resolution:
            assert perimeter_resolution > 0, 'perimeter_resolution must be strictly positive'
            ff["perimeterResolution"] = perimeter_resolution
        if relax:
            assert 0 <= relax <= 1, 'relax must be in [0, 1]'
            ff["relax"] = relax
        if min_speed:
            ff["minSpeed"] = min_speed
        if burned_map_layer:
            ff["bmapLayer"] = burned_map_layer

        self.ff = ff
    
    def __call__(
        self,
        nb_steps: int,
        step_size: float
    ):
        """
        Run the ForeFire simulation.
        Args:
            nb_step (int): number of step the simulation will execute
            step_size (float): duration (in seconds) between each step
        """
        pathes = []
        bournawt=[]
        times=[]
        for i in range(1, nb_steps+1):
            try:
                # Advance timestep by step_size
                logger.info("goTo[t=%f]" % (i*step_size))
                self.ff.execute("goTo[t=%f]" % (i*step_size))
                # Get pathes from previous execution
                newPathes = printToPathe(self.ff.execute("print[]"))
                pathes += newPathes
                bmap=self.ff.getDoubleArray("BMap")
                burnrbool = np.logical_not(np.isinf(bmap))
                # Count the True values in non_inf array
                burnr = np.sum(burnrbool*np.power(float(self.ff["minimalPropagativeFrontDepth"]),2))
                bournawt.append(burnr)
                times.append(i*step_size)

            except KeyboardInterrupt:
                # Keyboard interrupt in case simulation take a while and we want to show current state of simulation
                break

        return pathes
    

class UniformForeFireSimulation(ForeFireSimulation):
    """
    Class for a ForeFire simulation with uniform wind, uniform fuel (only one fuel type)
    and uniform slope.
    """
    def __init__(
        self,
        propagation_model: str,
        domain: Tuple[int],
        fuels_table: callable,
        horizontal_wind: float,
        vertical_wind: float,
        fuel_type: float,
        slope: float,
        fire_front: List[List[float]],
        spatial_increment: Optional[float] = None,
        minimal_propagative_front_depth: Optional[float] = None,
        perimeter_resolution: Optional[float] = None,
        relax: Optional[float] = None,
        min_speed: Optional[float] = None,
        burned_map_layer: Optional[int] = None,
        data_resolution: float = 1
    ):
        super().__init__(
            propagation_model, 
            domain, 
            fuels_table,
            spatial_increment,
            minimal_propagative_front_depth,
            perimeter_resolution,
            relax,
            min_speed,
            burned_map_layer,
            )
        
        # Instantiate domain
        domain_height, domain_width = domain[-1], domain[-2]
        domain_string = \
            f'FireDomain[sw=({self.ff["SWx"]},{self.ff["SWy"]},0);ne=({self.ff["SWx"] + self.ff["Lx"]},{self.ff["SWy"] + self.ff["Ly"]},0);t=0]'
        logger.info(domain_string)
        self.ff.execute(domain_string)

        # Propagation model layer
        self.ff.addLayer(
            "propagation",
            self.ff["propagationModel"],
            "propagationModel")
        logger.info(f'ROS model: {propagation_model}')

        # Wind layers
        self.ff["windU"] = horizontal_wind
        self.ff["windV"] = vertical_wind
        self.ff.addLayer("data","windU","windU")
        self.ff.addLayer("data","windV","windV")
        logger.info(f'Uniform wind conditions: horizontal wind: {horizontal_wind} m/s | vertical wind: {vertical_wind} m/s')

        # Fuel layer
        self.fuel_map = fuel_type * np.ones((1, 1, domain_height, domain_width))
        self.ff.addIndexLayer(
            "table", "fuel", 
            float(self.ff["SWx"]), float(self.ff["SWy"]), 0, domain_width, domain_height, 0, self.fuel_map)
        logger.info(f'Fuel map types: {list(np.unique(self.fuel_map))}')

        # Altitude layer
        slope = slope * math.pi / 180
        self.altitude_map = np.ones_like(self.fuel_map)
        assert domain_width % data_resolution == 0, "domain_width must be divisible by data_resolution"
        self.altitude_map[:, :, :] = np.linspace(0, domain_width, domain_width // data_resolution) * math.tan(slope)
        self.ff.addScalarLayer("table", "altitude", 0, 0, 0, domain_width, domain_height, 0, self.altitude_map)

        # Instantiate fire front (front orentation is clockwise!!)
        self.ff.execute(f"\tFireFront[id=2;domain=0;t=0]")
        for (xp, yp) in fire_front:
            self.ff.execute(f"\t\tFireNode[domain=0;loc=({xp},{yp},0);vel=(0,0,0);t=0;state=init;frontId=2]")
        logger.info(f'Initial fire front: {fire_front}')