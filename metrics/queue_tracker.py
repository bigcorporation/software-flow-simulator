# metrics/queue_tracker.py

class QueueTracker:
    def __init__(self, stages):
        self.wait_times = {stage: [] for stage in stages}
        self.queue_lengths = {stage: [] for stage in stages}
        self.last_queue_check_time = {stage: 0.0 for stage in stages}
        self.area_under_queue_curve = {stage: 0.0 for stage in stages}
        self.current_queue_length = {stage: 0.0 for stage in stages}

    def record_arrival(self, stage_name, env):
        return env.now

    def record_wait(self, stage_name, env, arrival_time):
        wait = env.now - arrival_time
        self.wait_times[stage_name].append(wait)

    def queue_update_area(self, stage_name, now):
        last_time = self.last_queue_check_time[stage_name]
        delta = now - last_time
        self.area_under_queue_curve[stage_name] += self.current_queue_length[stage_name] * delta
        self.last_queue_check_time[stage_name] = now

    def queue_enter(self, stage_name, now):
        self.queue_update_area(stage_name, now)
        self.current_queue_length[stage_name] += 1

    def queue_exit(self, stage_name, now):
        self.queue_update_area(stage_name, now)
        self.current_queue_length[stage_name] -= 1
