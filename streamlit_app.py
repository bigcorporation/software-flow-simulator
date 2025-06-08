# streamlit_app.py

import streamlit as st
from main_streamlit import run_simulation
from visualisation.plotter import plot_simulation_results

st.set_page_config(page_title="Development Sim", layout="wide")

st.title("Development Sim")
st.markdown("This sim models a software development process where work items enter from a backlog, flow through development, testing, test automation, then get released. It simulates limited developer and tester resources handling work with pull based priorities and possible rework based on failure chance.")
st.markdown("The model tracks key performance metrics such as work in progress, resource utilisation, flow efficiency, and wait times.")
st.markdown("Adjust the configuration, then select Run Simulation")


# --- Config inputs in expander ---
with st.expander("Configuration", expanded=True):

    st.markdown("##### Work Parameters")
    col3, col4, col5 = st.columns(3)

    with col3:
        num_work_items = st.number_input("Number of Work Items", min_value=1, value=300)

    with col4:
        failure_chance = st.number_input("Rework Chance", min_value=0.0, max_value=1.0, step=0.1, value=0.3)

    with col5:
        wip_limit = st.number_input("WIP Limit", min_value=1, value=8)

    st.markdown("##### Resources")
    col1, col2 = st.columns(2)

    with col1:
        num_developers = st.number_input("Number of Developers", min_value=1, value=4)
        num_testers = st.number_input("Number of Testers", min_value=1, value=2)

    with col2:
        developer_cost = st.number_input("Developer Hourly Cost ($)", min_value=1, value=150)
        
        tester_cost = st.number_input("Tester Hourly Cost ($)", min_value=1, value=120)

    st.markdown("##### Stage Durations (Hours)")
    col3, col4, col5 = st.columns(3)
    with col3:
        backlog = st.number_input("Backlog", min_value=0, value=0)
        develop = st.number_input("Develop", min_value=1, value=20)
    with col4:
        test = st.number_input("Test", min_value=1, value=8)
        rework = st.number_input("Rework", min_value=1, value=3)
    with col5:
        art = st.number_input("ART", min_value=1, value=2)
        release = st.number_input("Release", min_value=1, value=3)

# Assemble durations
durations = {
    "Backlog": backlog,
    "Develop": develop,
    "Test": test,
    "Rework": rework,
    "ART": art,
    "Release": release
}

# Assemble config with dynamic costs
config = {
    "num_developers": num_developers,
    "num_testers": num_testers,
    "failure_chance": failure_chance,
    "durations": durations,
    "num_work_items": num_work_items,
    "wip_limit": wip_limit,
    "costs": {
        "developers": developer_cost,
        "testers": tester_cost
    }
}

# --- Big central run button ---
st.markdown("<hr>", unsafe_allow_html=True)
run_clicked = st.button("**Run Simulation**", type="primary")

# --- Run simulation ---
if run_clicked:
    with st.spinner("Loading"):
        metrics, config_used, sim_time = run_simulation(config=config)

        st.write(f"**Simulation Time:** {sim_time:.0f} hours")
        st.write(f"**Items Developed:** {metrics.completed_items}")
        st.write(f"**Total Cost**: ${metrics.cost_tracker.compute_total_cost():,.2f}")

        fig = plot_simulation_results(metrics, config_used, sim_time)
        st.pyplot(fig)
        


