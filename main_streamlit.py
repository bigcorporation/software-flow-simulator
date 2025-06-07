import json
import os
import random
from visualisation import plotter
from simulator import Simulator
import matplotlib.pyplot as plt

def run_simulation(config=None, config_path="config.json"):
    if config is None:
        # Load config from file if no config dict provided
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, config_path)
        with open(full_path) as f:
            config = json.load(f)
    random.seed(42)

    sim = Simulator(config)
    sim.run_simulator()
    simulation_time = sim.env.now

    return sim.metrics, config, simulation_time

def print_results(metrics, config, simulation_time):
    print(f'=====Simulation Configuration=====\n')
    for key, value in config.items():
        print(f"{key}: {value}")
    
    print(f'\n=====Simulation Results=====')
    print(f'\nRun Time: {simulation_time} hours')
    print(f"Completed Items: {metrics.completed_items}")

def main():
    metrics, config, simulation_time = run_simulation()
    print_results(metrics, config, simulation_time)

    fig = plotter.plot_simulation_results(metrics, config, simulation_time)
    plt.show()

if __name__ == "__main__":
    main()
