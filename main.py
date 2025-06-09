import json
import os
import random
from visualisation import plotter
from simulator import Simulator
import matplotlib.pyplot as plt

def main():
    # Load config
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')

    with open(config_path) as f:
        config = json.load(f)

    random.seed(42)    
    
    # Run simulation
    sim = Simulator(config)
    sim.run_simulator()

    #Tracks end time of simulation
    simulation_time = sim.env.now

    # Now print your results using correct references:
    print(f'=====Simulation Configuration=====\n')
    for key, value in config.items():
        print(f"{key}: {value}")
    
    print(f'\n=====Simulation Results=====')
    print(f'\nRun Time: {simulation_time} hours')
    print(f"Completed Items: {sim.metrics.completed_items}")
    print(f"Total Cost: ${sim.team.cost_tracker.compute_total_cost():,.2f}")


    # Plot simulation results
    fig = plotter.plot_simulation_results(sim.metrics, config, sim.env.now)
    plt.show()  # Show the plots

if __name__ == "__main__":
    main()