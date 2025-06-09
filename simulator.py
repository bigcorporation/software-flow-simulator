import simpy
import random
from metrics import Metrics
from metrics.cost_tracker import CostTracker

class Team:
    def __init__(self, env, config, sim):
        self.env = env
        self.config = config
        self.sim = sim
        self.cost_tracker = CostTracker(config)
        self.developers = simpy.PriorityResource(env, capacity=config['num_developers'])
        self.testers = simpy.PriorityResource(env, capacity=config['num_testers'])
        self.business_analysts = simpy.PriorityResource(env, capacity=config['num_business_analysts'])
        self.stage_resources = {
            'Backlog': self.developers,
            'Develop': self.developers,
            'Smoke_Test': self.business_analysts,
            'Test': self.testers,
            'Rework': self.developers,
            'ART': self.developers,
            'Release': self.developers
        }
        self.stage_priorities = {
            'Release': 0,
            'ART': 1,
            'Rework': 2,
            'Test': 3,
            'Smoke_Test': 4,
            'Develop': 5,
            'Backlog': 6
        }

class WorkItem:
    def __init__(self, env, team, config, metrics):
        self.env = env
        self.team = team
        self.config = config
        
        self.metrics = metrics
        self.active_time = 0
        self.action = env.process(self.run_workflow())

    def process_stage(self, stage_name, duration):
        resource = self.team.stage_resources[stage_name]
        priority = self.team.stage_priorities[stage_name]
        
        arrival = self.metrics.record_arrival(stage_name, self.env)
        self.metrics.queue_enter(stage_name, self.env.now)
        
        with resource.request(priority=priority) as req:
            yield req
            start_time = self.env.now
            self.metrics.record_wait(stage_name, self.env, arrival)
            self.metrics.queue_exit(stage_name, self.env.now)
            
            yield self.env.timeout(duration)
            self.metrics.log_resource_utilisation(stage_name, start_time, self.env.now)
            self.active_time += duration if stage_name != 'Backlog' else 0

    def run_workflow(self):
        cfg = self.config['durations']
        yield from self.process_stage('Backlog', cfg['Backlog'])

        yield self.team.sim.wip.put(1)  #Wait here if WIP limit is reached
        self.metrics.log_wip(self.env, +1)
        self.entry_time = self.env.now
        

        yield from self.process_stage('Develop', cfg['Develop'])
        yield from self.process_stage('Smoke_Test', cfg['Smoke_Test'])

        if random.random() < self.config['smoke_test_failure_chance']:
            yield from self.process_stage('Rework', cfg['Rework'])
            yield from self.process_stage('Smoke_Test', cfg['Smoke_Test'])

        yield from self.process_stage('Test', cfg['Test'])

        if random.random() < self.config['test_failure_chance']:
            yield from self.process_stage('Rework', cfg['Rework'])
            yield from self.process_stage('Test', cfg['Test'])

        yield from self.process_stage('ART', cfg['ART'])
        yield from self.process_stage('Release', cfg['Release'])
        self.metrics.log_wip(self.env, -1)
        self.metrics.completed_items += 1
        self.metrics.item_exit(self.entry_time, self.active_time, self.env)
        yield self.team.sim.wip.get(1)  # Release WIP slot

class Simulator:
    def __init__(self, config):
        self.env = simpy.Environment()
        self.config = config
        self.team = Team(self.env, config, sim=self)
        self.metrics = Metrics(self.team)
        self.cost_tracker = CostTracker(config)

        self.metrics.cost_tracker = self.cost_tracker
        self.wip = simpy.Container(self.env, init=0, capacity=config["wip_limit"])


    def run_simulator(self):
        for _ in range(self.config['num_work_items']):
            WorkItem(self.env, self.team, self.config, self.metrics)
        self.env.run()
        total_time = self.env.now
        self.metrics.cost_tracker.set_simulation_time(total_time)