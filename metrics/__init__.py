from .queue_tracker import QueueTracker
from .wip_tracker import WIPTracker
from .cost_tracker import CostTracker

class Metrics:
    def __init__(self, team):
        self.team = team
        stages = list(team.stage_resources.keys())

        # Delegate queue, wip tracking, and cost tracking to these helpers
        self.queue_tracker = QueueTracker(stages)
        self.wip_tracker = WIPTracker()
        self.cost_tracker = CostTracker(team.config)


        # Additional metrics storage
        self.utilisation = {'Developers_busy_time': 0.0, 'Testers_busy_time': 0.0}
        self.completed_items = 0

        # Flow efficiency tracking
        self.item_times = []

    # Queue tracking delegations
    def record_arrival(self, stage_name, env):
        return self.queue_tracker.record_arrival(stage_name, env)

    def record_wait(self, stage_name, env, arrival_time):
        self.queue_tracker.record_wait(stage_name, env, arrival_time)

    def queue_enter(self, stage_name, now):
        self.queue_tracker.queue_enter(stage_name, now)

    def queue_exit(self, stage_name, now):
        self.queue_tracker.queue_exit(stage_name, now)

    # WIP tracking delegation
    def log_wip(self, env, delta):
        self.wip_tracker.log_wip(env, delta)

    # Resource utilization
    def log_resource_utilisation(self, stage_name, start_time, end_time):
        resource = self.team.stage_resources[stage_name]
        busy_time = end_time - start_time
        if resource == self.team.developers:
            self.utilisation['Developers_busy_time'] += busy_time
        elif resource == self.team.testers:
            self.utilisation['Testers_busy_time'] += busy_time

    # Flow efficiency helpers
    def item_exit(self, entry_time, active_time, env):
        lead_time = env.now - entry_time
        self.item_times.append((lead_time, active_time))

    def get_flow_efficiency(self):
        efficiencies = [
            (active / lead) if lead > 0 else 0
            for lead, active in self.item_times
        ]
        return sum(efficiencies) / len(efficiencies) if efficiencies else 0.0
