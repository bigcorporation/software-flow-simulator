import simpy
import random
from metrics import Metrics

class Team:
    def __init__(self, env, config):
        self.env = env
        self.config = config
        self.developers = simpy.PriorityResource(env, capacity=config['num_developers'])
        self.testers = simpy.PriorityResource(env, capacity=config['num_testers'])
        self.stage_resources = {
            'Backlog': self.developers,
            'Develop': self.developers,
            'Test': self.testers,
            'Rework': self.developers,
            'Regression': self.developers,
            'Release': self.developers
        }
        self.stage_priorities = {
            'Release': 0,
            'Regression': 1,
            'Rework': 2,
            'Test': 3,
            'Develop': 4,
            'Backlog': 5
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
        self.metrics.log_wip(self.env, +1)
        self.entry_time = self.env.now
        
        yield from self.process_stage('Develop', cfg['Develop'])
        yield from self.process_stage('Test', cfg['Test'])

        if random.random() < self.config['failure_chance']:
            yield from self.process_stage('Rework', cfg['Rework'])
            yield from self.process_stage('Test', cfg['Test'])

        yield from self.process_stage('Regression', cfg['Regression'])
        yield from self.process_stage('Release', cfg['Release'])
        self.metrics.log_wip(self.env, -1)
        self.metrics.completed_items += 1
        self.metrics.item_exit(self.entry_time, self.active_time, self.env)

class Simulator:
    def __init__(self, config):
        self.env = simpy.Environment()
        self.config = config
        self.team = Team(self.env, config)
        self.metrics = Metrics(self.team)  # You'll need to import Metrics

    def run_simulator(self):
        for _ in range(self.config['num_work_items']):
            WorkItem(self.env, self.team, self.config, self.metrics)
        self.env.run()