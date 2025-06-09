# metrics/cost_tracker.py

class CostTracker:
    def __init__(self, config):
        self.config = config
        self.simulation_time = 0

    def set_simulation_time(self, sim_time):
        self.simulation_time = sim_time

    def compute_total_cost(self):
        devs = self.config['num_developers']
        testers = self.config['num_testers']
        business_analysts = self.config['num_business_analysts']
        dev_cost = self.config['costs']['developers']
        tester_cost = self.config['costs']['testers']
        business_analyst_cost = self.config['costs']['business_analysts']

        total_cost = (
            self.simulation_time * devs * dev_cost +
            self.simulation_time * testers * tester_cost +
            self.simulation_time * business_analysts * business_analyst_cost
        )
        return total_cost
