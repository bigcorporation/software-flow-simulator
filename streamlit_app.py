# streamlit_app.py

import streamlit as st
from main_streamlit import run_simulation
from visualisation.plotter import plot_simulation_results

st.set_page_config(page_title="SimPy Dev/Test Simulation", layout="wide")

st.title("Development Simulation")
st.markdown("This simulation models a software development process where work items flow through development, testing, and release from a backlog. It simulates limited developer and tester resources handling work with pull based priorities and possible rework based on failure chance.")
st.markdown("The system tracks key performance metrics such as work in progress, resource utilisation, flow efficiency, and queue times.")

# --- Sidebar config ---
st.sidebar.header("Simulation Settings")

# Basic config inputs
num_developers = st.sidebar.number_input("Number of Developers", min_value=1, value=4)
num_testers = st.sidebar.number_input("Number of Testers", min_value=1, value=2)
failure_chance = st.sidebar.slider("Failure Chance", 0.0, 1.0, 0.3, step=0.05)
num_work_items = st.sidebar.number_input("Number of Work Items", min_value=1, value=300)

# Stage durations
st.sidebar.markdown("### Stage Durations (hours)")
durations = {
    "Backlog": st.sidebar.number_input("Backlog", min_value=0, value=0),
    "Develop": st.sidebar.number_input("Develop", min_value=1, value=20),
    "Test": st.sidebar.number_input("Test", min_value=1, value=8),
    "Rework": st.sidebar.number_input("Rework", min_value=1, value=3),
    "Regression": st.sidebar.number_input("Regression", min_value=1, value=2),
    "Release": st.sidebar.number_input("Release", min_value=1, value=3)
}

# Bundle config
config = {
    "num_developers": num_developers,
    "num_testers": num_testers,
    "failure_chance": failure_chance,
    "durations": durations,
    "num_work_items": num_work_items
}

# --- Run button ---
if st.sidebar.button("Run Simulation"):
    with st.spinner("Running simulation..."):
        metrics, config_used, sim_time = run_simulation(config=config)

        st.write(f"Simulation Time: {sim_time:.0f} hours")
        st.write(f"Items Developed: {metrics.completed_items}")


        fig = plot_simulation_results(metrics, config_used, sim_time)
        st.pyplot(fig)
