
Development Flow Simulation & Optimiser
======================================

This project simulates a software delivery pipeline to evaluate how different team configurations (developers, business analysts, testers)
and WIP limits impact delivery performance and cost. There are two Streamlit apps to provide a visual interface. The Explorer app allows users to trial different configurations and view results. The Optimiser allows users to configure a project and its deadline, then optimise to minimise cost, varying resources and WIP limits.

Purpose
-------
The simulator is designed to help Agile software teams:

- Understand the cost and throughput implications of team size and WIP policy.
- Explore trade-offs between speed, cost, and delivery predictability.
- Identify the most cost-efficient configuration that meets a delivery deadline.

How It Works
------------
The simulation models the flow of work items through a multi-stage software development process:

1. Stages:
   - Backlog → Develop → Smoke Test → Test → ART → Release
2. Resources:
   - Developers, business analysts, and testers are assigned to relevant stages.
3. Work Items:
   - Items are processed sequentially through the stages.
   - Each stage has configurable duration and resource constraints.
   - Failures can occur in smoke testing and testing (e.g., 30% chance), sending items to Rework.

4. Simulation Engine:
   - Built with SimPy, a discrete-event simulation framework.
   - Tracks metrics like time in system, WIP, queue lengths, and cost.

Configuration
-------------
Settings are defined in config.json or adjustable in the Streamlit interface:

- num_developers: Number of developers
- num_testers: Number of testers
- num_business_analysts: Number of business analysts
- wip_limit: Max number of items in progress at once
- durations: Stage durations in hours
- num_work_items: Total items to simulate
- smoke_test_failure_chance: Likelihood of failure during smoke testing triggering rework
- test_failure_chance: Likelihood of failure during testing triggering rework
- developer_cost, tester_cost, business_analyst_cost: Hourly rates
- delivery_weeks: Delivery deadline converted to hours

Outputs
-------
After each run, you’ll see:

- Best Configuration:
  - Developers, testers, WIP limit
  - Cost per item, total cost, completion time
- Metrics:
  - Number of completed items
  - Simulation time
- Visualisations:
  - WIP over time
  - Queue lengths
  - Cost breakdown
  - Parallel coordinates plot of configuration space

Optimisation
------------
The streamlit_app_opt.py script runs a grid search over user-defined ranges for:

- Developers (e.g., 1–10)
- Testers (e.g., 1–10)
- WIP limit (e.g., 1–20)

It evaluates each configuration and selects the one with the lowest cost per item while meeting the delivery deadline.

How to Run
----------

Option 1: Run Locally

    pip install -r requirements.txt
    streamlit run streamlit_app.py
    # or
    streamlit run streamlit_app_opt.py  # for optimiser interface

Option 2: Run on Streamlit

Optimiser
https://optimiser-software-development-flow.streamlit.app/

Explorer
https://explorer-development-flow-simulator.streamlit.app/

Limitations
-----------

- Optimiser uses grid search, which can be slow for large parameter ranges.
- Assumes uniform task durations and failure chances.
- All items follow the same fixed sequence of stages.
- Does not model parallel task dependencies or backlog prioritisation.
- Assumes pull based priorities adhered to perfectly (not preemptive).

Project Structure
-----------------

    ├── config.json
    ├── main.py
    ├── simulator.py               # Core SimPy logic
    ├── main_streamlit.py			  	
    ├── streamlit_app.py           # Explorer interface
    ├── streamlit_app_opt.py       # Optimisation interface
    ├── metrics/                   # Tracks WIP, queues, cost
    ├── visualisation/             # Custom plotting (e.g., matplotlib)
    ├── requirements.txt
