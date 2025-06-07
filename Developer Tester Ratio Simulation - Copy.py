import simpy
import random
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import numpy as np 




#Global Lists, Variables
stages = ['Backlog', 'Develop', 'Test', 'Rework', 'Regression','Release']



#Metric tracking class with helper functions to manage metrics
class Metrics:
    def __init__(self, team):

        self.wait_times = {stage: [] for stage in stages}
        self.queue_lengths = {stage: [] for stage in stages}
        self.utilisation = {'Developers_busy_time': 0.0, 'Testers_busy_time': 0.0}
        self.completed_items = 0

        # Time-weighted queue tracking
        self.last_queue_check_time = {stage: 0.0 for stage in stages}
        self.area_under_queue_curve = {stage: 0.0 for stage in stages}
        self.current_queue_length = {stage: 0.0 for stage in stages}

        #TO DO find terminology for what im doing here
        self.team = team
           
        #WIP Tracking
        self.wip_log = []       #List of time, wip tuples
        self.current_wip = 0    #Current number of WIP in the system

        #Flow Efficiency
        self.item_times = []

    
    #Wait Times
    def record_arrival( self, stage_name, env):                 #Called when item arrives in queue
        return env.now
    
    def record_wait(self, stage_name, env, arrival_time):      #Called after resource granted
        wait = env.now - arrival_time
        self.wait_times[stage_name].append(wait)

    #Resource Utilisation
    def log_resource_utilisation(self, stage_name, start_time, end_time):
        resource = self.team.stage_resources[stage_name]
        busy_time = end_time - start_time
        if resource == self.team.developers:
            self.utilisation['Developers_busy_time'] += (busy_time)
        elif resource == self.team.testers:
            self.utilisation['Testers_busy_time'] += (busy_time)

    #Work In Progress (WIP)
    def log_wip(self, env, delta):
        self.current_wip += delta
        self.wip_log.append((env.now, self.current_wip))
    
    #Queue Helpers
    #Update queue area
    def queue_update_area(self, stage_name, now):
        last_time = self.last_queue_check_time[stage_name]
        delta = now - last_time
        self.area_under_queue_curve[stage_name] += self.current_queue_length[stage_name] * delta
        self.last_queue_check_time[stage_name] = now

    #Increment queue
    def queue_enter(self, stage_name, now):
        self.queue_update_area(stage_name, now)
        self.current_queue_length[stage_name] += 1

    #Decrement queue
    def queue_exit(self, stage_name, now):
        self.queue_update_area(stage_name, now)
        self.current_queue_length[stage_name] -= 1

    #Flow Efficiency Helpers
    #Enter time
    def item_enter(self, env):
        return env.now
    
    def item_active_time(self, stage_name, active_time):
        if stage_name == 'Backlog':
            return 0
        if stage_name in stages:
            return active_time
        else:
            return 0
    
    def item_exit(self, entry_time, active_time, env):
        lead_time = env.now - entry_time
        self.item_times.append((lead_time, active_time))

    def get_flow_efficiency(self):
        efficiencies = [
            active / lead if lead > 0 else 0
            for lead, active in self.item_times
        ]
        return sum(efficiencies) / len(efficiencies) if efficiencies else 0.0


#Team class to manage workers, who works where, and what priority each station it
class Team:
    def __init__(self, env, config):
        self.env = env
        self.config = config
        #Developer and tester capacity set in configuration
        self.developers = simpy.PriorityResource(env, capacity=config['num_developers'])
        self.testers = simpy.PriorityResource(env, capacity=config['num_testers'])
        #Define which stations resources can serve requests
        self.stage_resources = {
            'Backlog': self.developers,
            'Develop': self.developers,
            'Rework': self.developers,
            'Regression': self.developers,
            'Release': self.developers,
            'Test': self.testers
        }
        self.stage_priorities = {
            'Release': 0,
            'Regression': 1,
            'Rework': 2,
            'Test': 3,
            'Develop': 4,
            'Backlog': 5
        }

#Setup resource requests (work items) and define generators in environment using team, config, and metric attributes
class WorkItem:
    def __init__(self, env, team, config, metrics):
        self.env = env
        self.team = team
        self.config = config
        self.metrics = metrics
        self.active_time = 0
        self.action = env.process(self.run_workflow())

    #Generator function which manages how work items are processed at a single stage
    def process_stage(self, stage_name, duration):
        resource = self.team.stage_resources[stage_name]
        priority = self.team.stage_priorities[stage_name]

        #Item arrives, record arrival time and increment queue
        now = self.env.now
        arrival = self.metrics.record_arrival(stage_name, self.env)
        self.metrics.queue_enter(stage_name, now)

        
        with resource.request(priority=priority) as req:
            yield req
            
            #Resource granted, update wait time, decrement queue, start tracking utilisation time
            start_time = self.env.now
            now = self.env.now
            self.metrics.record_wait(stage_name, self.env, arrival)
            self.metrics.queue_exit(stage_name, now)

            yield self.env.timeout(duration)
            
            #Item processed, update wait time, stop tracking utilisation time, update active time with stage duration
            end_time = self.env.now
            self.metrics.log_resource_utilisation(stage_name, start_time, end_time)
            self.active_time += self.metrics.item_active_time(stage_name, duration)
    
    #Generator function which manages work items through the workflow
    #Define sequence of stations including failure chance and its workflow
    def run_workflow(self):
        cfg = self.config['durations']

        yield from self.process_stage('Backlog', cfg['Backlog'])
        #Item enters development stream, increment WIP, set active time to 0 and start tracking
        self.metrics.log_wip(self.env, +1)
        self.active_time = 0
        self.entry_time = self.metrics.item_enter(self.env)
        

        yield from self.process_stage('Develop', cfg['Develop'])
        yield from self.process_stage('Test', cfg['Test'])

        if random.random() < self.config['failure_chance']:
            yield from self.process_stage('Rework', cfg['Rework'])
            yield from self.process_stage('Test', cfg['Test'])

        yield from self.process_stage('Regression', cfg['Regression'])
        yield from self.process_stage('Release', cfg['Release'])
        #Item leaves development stream, decrease WIP and increment completed items, update lead time
        self.metrics.log_wip(self.env, -1)
        self.metrics.completed_items += 1
        self.metrics.item_exit(self.entry_time, self.active_time, self.env)
        

#Class to manage all simulation components. Seperate from work item, resource, and metric logic
class Simulator:

    #Initiate environment and integrate config, metrics, and team
    def __init__(self, config):
        self.env = simpy.Environment()
        self.config = config
        self.team = Team(self.env, config)
        self.metrics = Metrics(self.team)
    
    def monitor_completion(self):
        while True:
            if self.metrics.completed_items >= self.config['num_work_items']:
                break
            yield self.env.timeout(1)

    #Generator function to initiate the work item process and control sim runtime via config
    def run_simulator(self):
        for _ in range(self.config['num_work_items']):
            WorkItem(self.env, self.team, self.config, self.metrics)
        self.env.process(self.monitor_completion())
        self.env.run()


#Create the simulator instance according to config
sim = Simulator(config)

#Starts the simulation by calling run()
sim.run_simulator()

#Tracks end time of simulation
simulation_time = sim.env.now

# === PRINT METRICS ===
print(f'=====Simulation Configuration=====\n')
for key, value in config.items():
    print(f"{key}: {value}")
print(f'\n=====Simulation Results=====')
print(f'\nRun Time: {simulation_time} hours')
print(f"Completed Items: {sim.metrics.completed_items}")
print('\n-----Resource Utilisation-----')
print(f"Developers Utilisation: {sim.metrics.utilisation['Developers_busy_time'] / (config['num_developers'] * simulation_time):.2%}")
print(f"Testers Utilisation: {sim.metrics.utilisation['Testers_busy_time'] / (config['num_testers'] * simulation_time):.2%}")
print("\n------Average Wait Time------")
for stage, waits in sim.metrics.wait_times.items():
    avg_wait = sum(waits) / len(waits) if waits else 0
    print(f"{stage}: {avg_wait:.2f} hours")
print("\n------Average Queue Length------")
for stage, area in sim.metrics.area_under_queue_curve.items():
    avg_queue = area / simulation_time
    print(f"{stage}: {avg_queue:.2f}")




# === SETUP SUBPLOTS ===
fig, axs = plt.subplots(2, 2, figsize=(14, 10))
axs = axs.flatten()

# # === WIP Over Time Plot ===
# times, wip_counts = zip(*sim.metrics.wip_log) if sim.metrics.wip_log else ([0], [0])
# ax = axs[0]
# ax.step(times, wip_counts, where='post', color='darkgreen')
# ax.set_xlabel('Simulation Time (hours)')
# ax.set_ylabel('WIP (Items in System)')
# ax.set_title('Work In Progress Over Time')
# ax.grid(True, linestyle='--', alpha=0.7)

ax = axs[0]
times, wip_counts = zip(*sim.metrics.wip_log) if sim.metrics.wip_log else ([0], [0])

# Set thresholds based on dev capacity
total_capacity = config['num_developers']  # Main capacity baseline

green_thresh = 1.0 * total_capacity      # Green = WIP ≤ number of developers
orange_thresh = 1.2 * total_capacity    # Orange = up to 120% overload

def get_color(value):
    if value <= green_thresh:
        return "green"
    elif value <= orange_thresh:
        return "orange"
    else:
        return "red"

for i in range(1, len(times)):
    x0, x1 = times[i - 1], times[i]
    y0, y1 = wip_counts[i - 1], wip_counts[i]

    color = get_color(y0)
    ax.plot([x0, x1], [y0, y0], color=color, linewidth=1)

    if y0 != y1:
        vcolor = get_color(y1)
        ax.plot([x1, x1], [y0, y1], color=vcolor, linewidth=1)

ax.set_xlabel('Simulation Time (hours)')
ax.set_ylabel('WIP (Items in System)')
ax.set_title('Work In Progress Over Time')
ax.grid(True, linestyle='--', alpha=0.7)

# === Utilisation Plot ===
dev_util = sim.metrics.utilisation['Developers_busy_time'] / (config['num_developers'] * simulation_time)
test_util = sim.metrics.utilisation['Testers_busy_time'] / (config['num_testers'] * simulation_time)
resources = ['Developers', 'Testers']
utilisation = [dev_util, test_util]

ax = axs[1]
ax.bar(resources, utilisation, color=['darkblue', 'grey'])
ax.set_ylim(0, 1)
ax.set_ylabel('Utilisation')
ax.set_title('Resource Utilisation')
ax.grid(axis='y', linestyle='--', alpha=0.7)
for i, util in enumerate(utilisation):
    ax.text(i, util + 0.02, f"{util:.1%}", ha='center', va='bottom', fontsize=10)

# Flow Efficiency Histogram
efficiencies = [
    a / l if l > 0 else 0
    for l, a in sim.metrics.item_times
]

ax = axs[2]  # Replace or add new slot

# Use 10 bins
num_bins = 10
counts, bins, patches = ax.hist(efficiencies, bins=num_bins, edgecolor='black')

# Create a colormap from red -> orange -> green
cmap = mcolors.LinearSegmentedColormap.from_list("efficiency_gradient", ["red", "orange", "green"])
norm = mcolors.Normalize(vmin=0, vmax=num_bins - 1)

# Apply the gradient color to each bin
for i, patch in enumerate(patches):
    patch.set_facecolor(cmap(norm(i)))

# Labels and grid
ax.set_title('Flow Efficiency Distribution')
ax.set_xlabel('Efficiency')
ax.set_ylabel('Work Item Count')
ax.grid(True, linestyle='--', alpha=0.7)

# Labels and formatting
ax.set_title('Flow Efficiency Distribution')
ax.set_xlabel('Efficiency')
ax.set_ylabel('Work Item Count')
ax.grid(True, linestyle='--', alpha=0.7)



# === Wait Time Plot ===
stages = list(sim.metrics.wait_times.keys())
avg_waits = [sum(w) / len(w) if w else 0.0 for w in sim.metrics.wait_times.values()]

ax = axs[3]
bars = ax.bar(stages, avg_waits, color='slateblue')
ax.set_ylabel('Average Wait Time (hours)')
ax.set_title('Average Wait Time per Stage')
ax.grid(axis='y', linestyle='--', alpha=0.7)
for bar, wait in zip(bars, avg_waits):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
            f"{wait:.2f}", ha='center', va='bottom', fontsize=9)

# # === Queue Length Plot ===
# avg_queue_lengths = {
#     stage: area / simulation_time
#     for stage, area in sim.metrics.area_under_queue_curve.items()
# }
# stages = list(avg_queue_lengths.keys())
# queue_lengths = list(avg_queue_lengths.values())

# ax = axs[2]
# bars = ax.bar(stages, queue_lengths, color='indianred')
# ax.set_ylabel('Average Queue Length')
# ax.set_title('Average Queue Length per Stage')
# ax.grid(axis='y', linestyle='--', alpha=0.6)
# ax.set_ylim(0, max(queue_lengths) * 1.2 if queue_lengths else 1)
# for bar, val in zip(bars, queue_lengths):
#     ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
#             f"{val:.2f}", ha='center', va='bottom')

# === Final Layout and Show ===
plt.tight_layout()
plt.show()

