import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches

def plot_simulation_results(metrics, config, simulation_time):
    # Access wait_times through the queue_tracker
    stages = list(metrics.queue_tracker.wait_times.keys())
    
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    axs = axs.flatten()

    # --- WIP Over Time Plot ---
    ax = axs[0]
    times, wip_counts = zip(*metrics.wip_tracker.wip_log) if metrics.wip_tracker.wip_log else ([0], [0])

    total_capacity = config['num_developers']
    green_thresh = 1.0 * total_capacity
    orange_thresh = 1.2 * total_capacity

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
    ax.set_title('WIP Over Time')
    ax.grid(True, linestyle='--', alpha=0.7)

    # Add legend for WIP
    wip_legend_patches = [
        mpatches.Patch(color='green', label=f'WIP ≤ {green_thresh:.0f}'),
        mpatches.Patch(color='orange', label=f'{green_thresh:.0f} < WIP ≤ {orange_thresh:.0f}'),
        mpatches.Patch(color='red', label=f'WIP > {orange_thresh:.0f}')
    ]
    ax.legend(handles=wip_legend_patches, title='WIP Levels')

    # --- Resource Utilisation Plot with Warnings ---
    ax = axs[1]
    dev_util = metrics.utilisation['Developers_busy_time'] / (config['num_developers'] * simulation_time)
    test_util = metrics.utilisation['Testers_busy_time'] / (config['num_testers'] * simulation_time)
    resources = ['Developers', 'Testers']
    utilisation = [dev_util, test_util]

    def util_color(util):
        if util <= 0.80:
            return 'green'
        elif util <= 0.95:
            return 'orange'
        else:
            return 'red'

    colors = [util_color(u) for u in utilisation]

    bars = ax.bar(resources, utilisation, color=colors)
    ax.set_ylim(0, 1)
    ax.set_ylabel('Utilisation')
    ax.set_title('Resource Utilisation')
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    for i, (bar, util) in enumerate(zip(bars, utilisation)):
        ax.text(i, util + 0.02, f"{util:.1%}", ha='center', va='bottom', fontsize=10)

    # Add legend for Utilisation
    util_legend_patches = [
        mpatches.Patch(color='green', label='Low (≤ 80%)'),
        mpatches.Patch(color='orange', label='Moderate (80%-95%)'),
        mpatches.Patch(color='red', label='High (> 95%)')
    ]
    ax.legend(handles=util_legend_patches, title='Utilisation Levels')

    # --- Flow Efficiency Histogram ---
    ax = axs[2]
    efficiencies = [
        a / l if l > 0 else 0
        for l, a in metrics.item_times
    ]

    num_bins = 4
    counts, bins, patches = ax.hist(efficiencies, bins=num_bins, edgecolor='black')

    cmap = mcolors.LinearSegmentedColormap.from_list("efficiency_gradient", ["red", "orange", "green"])
    norm = mcolors.Normalize(vmin=0, vmax=num_bins - 1)

    for i, patch in enumerate(patches):
        patch.set_facecolor(cmap(norm(i)))

    ax.set_title('Flow Efficiency Distribution')
    ax.set_xlabel('Efficiency')
    ax.set_ylabel('Work Item Count')
    ax.grid(True, linestyle='--', alpha=0.7)

    # Define your 4 labels for bins
    labels = ['Very Low', 'Low', 'Medium', 'High']

    # Get colors from your colormap for each bin
    colors = [cmap(norm(i)) for i in range(num_bins)]

    # Create legend patches
    legend_patches = [mpatches.Patch(color=colors[i], label=labels[i]) for i in range(num_bins)]

    # Add legend to the same axis as your histogram
    ax.legend(handles=legend_patches, title='Flow Efficiency', loc='upper right')

    # # Add colorbar for flow efficiency gradient
    # sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    # sm.set_array([])
    # cbar = fig.colorbar(sm, ax=ax, orientation='vertical', fraction=0.046, pad=0.04)
    # cbar.set_label('Bin Index (Efficiency Gradient)')

    # --- Average Wait Time per Stage without Backlog ---
    ax = axs[3]

    # Filter out backlog stage
    filtered_stages = [s for s in stages if s.lower() != "backlog"]
    filtered_waits = [
        (sum(metrics.queue_tracker.wait_times[s]) / len(metrics.queue_tracker.wait_times[s]) if metrics.queue_tracker.wait_times[s] else 0.0)
        for s in filtered_stages
    ]

    min_wait = min(filtered_waits) if filtered_waits else 0
    max_wait = max(filtered_waits) if filtered_waits else 1  # avoid zero range

    def wait_color(wait):
        if max_wait == min_wait:
            return 'green'
        
        threshold1 = min_wait + (max_wait - min_wait) * 0.33
        threshold2 = min_wait + (max_wait - min_wait) * 0.66

        if wait <= threshold1:
            return 'green'
        elif wait <= threshold2:
            return 'orange'
        else:
            return 'red'

    colors = [wait_color(w) for w in filtered_waits]

    bars = ax.bar(filtered_stages, filtered_waits, color=colors)
    ax.set_ylabel('Average Wait Time (hours)')
    ax.set_title('Average Wait Time')
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    for bar, wait in zip(bars, filtered_waits):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"{wait:.2f}", ha='center', va='bottom', fontsize=9)

    # Add legend for Wait Times
    wait_legend_patches = [
        mpatches.Patch(color='green', label='Low'),
        mpatches.Patch(color='orange', label='Moderate'),
        mpatches.Patch(color='red', label='High')
    ]
    ax.legend(handles=wait_legend_patches, title='Wait Time')

    plt.tight_layout()
    return fig
