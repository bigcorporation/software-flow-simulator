# metrics/wip_tracker.py

class WIPTracker:
    def __init__(self):
        self.wip_log = []       # List of time, wip tuples
        self.current_wip = 0    # Current number of WIP in the system

    def log_wip(self, env, delta):
        self.current_wip += delta
        self.wip_log.append((env.now, self.current_wip))
