import streamlit as st
import itertools
from main_streamlit import run_simulation
from visualisation.plotter import plot_simulation_results
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Development Sim Optimiser", layout="wide")

st.title("Development Sim Optimiser")
st.markdown("""
This simulation models a software delivery pipeline to evaluate how different team sizes and WIP limits impact cost and throughput.
It uses grid search to find the most cost-effective configuration that completes all work items within a 
user-defined delivery deadline.
""")

# --- Fixed parameters ---
failure_chance = 0.3
durations = {
    "Backlog": 0,
    "Develop": 20,
    "Test": 8,
    "Rework": 2,
    "ART": 2,
    "Release": 3,
}

# --- Configurable inputs ---
st.markdown("### Configuration")
num_work_items = st.number_input("Number of Work Items", min_value=1, value=100)
developer_cost = st.number_input("Developer Hourly Cost ($)", min_value=1, value=150)
tester_cost = st.number_input("Tester Hourly Cost ($)", min_value=1, value=120)
delivery_weeks = st.number_input("Delivery Deadline (weeks)", min_value=1, value=12)

# Convert weeks to hours (5 days per week, 8 hours per day)
delivery_deadline_hours = delivery_weeks * 5 * 8

# --- Grid search ranges ---
st.markdown("### Grid Search Ranges")
dev_min, dev_max = st.slider("Developers", 1, 8, (1, 8))
tester_min, tester_max = st.slider("Testers", 1, 8, (1, 8))
wip_min, wip_max = st.slider("WIP Limit", 1, 20, (1, 20))

st.markdown("---")

run_opt = st.button("Run Optimiser", type="primary")

if run_opt:
    all_configs = list(itertools.product(
        range(dev_min, dev_max + 1),
        range(tester_min, tester_max + 1),
        range(wip_min, wip_max + 1)
    ))

    best_cost = float('inf')
    best_metrics = None
    best_config = None
    best_sim_time = None

    results_table = []
    total_configs = len(all_configs)
    skipped_configs = 0

    progress_bar = st.progress(0)

    for i, (num_developers, num_testers, wip_limit) in enumerate(all_configs):
        config = {
            "num_developers": num_developers,
            "num_testers": num_testers,
            "wip_limit": wip_limit,
            "failure_chance": failure_chance,
            "durations": durations,
            "num_work_items": num_work_items,
            "costs": {
                "developers": developer_cost,
                "testers": tester_cost
            }
        }

        metrics, config_used, sim_time = run_simulation(config=config)

        # --- Time constraint check ---
        if sim_time > delivery_deadline_hours:
            skipped_configs += 1
            progress_bar.progress((i + 1) / total_configs)
            continue

        cost = metrics.cost_tracker.compute_total_cost()
        completed = metrics.completed_items
        cost_per_item = cost / max(completed, 1)

        results_table.append({
            "Developers": num_developers,
            "Testers": num_testers,
            "WIP Limit": wip_limit,
            "Avg Cost": round(cost),
            "Avg Completed": completed,
            "Cost per Item": round(cost_per_item, 2),
            "Time (hrs)": round(sim_time)
        })

        if cost_per_item < best_cost:
            best_cost = cost_per_item
            best_metrics = metrics
            best_config = config_used
            best_sim_time = sim_time

        progress_bar.progress((i + 1) / total_configs)

    if len(results_table) == 0:
        st.warning("No configurations met the delivery deadline. Try increasing the number of weeks or expanding resource ranges.")
    else:
        if skipped_configs > 0:
            st.info(f"{skipped_configs} configurations skipped for exceeding the delivery deadline of {delivery_weeks} weeks.")

        # --- Show Best Config ---
        st.write("**Given**")
        st.write(f"Developer Cost: ${developer_cost}/hour")
        st.write(f"Tester Cost: ${tester_cost}/hour")
        st.write(f"Delivery Deadline: {delivery_weeks} weeks = {delivery_deadline_hours} hours")

        st.write("**Optimal Configuration**")
        st.write(f"Developers: {best_config['num_developers']}")
        st.write(f"Testers: {best_config['num_testers']}")
        st.write(f"WIP Limit: {best_config['wip_limit']}")

        st.markdown("**Metrics**")
        st.write(f"Simulation Time: {best_sim_time:.0f} hours")
        st.write(f"Total Cost: ${int(best_metrics.cost_tracker.compute_total_cost()):,}")
        st.write(f"Items Developed: {best_metrics.completed_items}")

        # --- Plot Results ---
        fig = plot_simulation_results(best_metrics, best_config, best_sim_time)
        st.pyplot(fig)

        # # --- Table of all results ---
        # st.markdown("**All Evaluated Configurations**")
        # results_table_sorted = sorted(results_table, key=lambda x: x["Cost per Item"])
        # st.dataframe(results_table_sorted, use_container_width=True)
