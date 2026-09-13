# Port Operations Copilot — Source Code Structure

This directory contains the production-grade source code for the **Port Operations Copilot** system.

```
src/
├── app.py                     # Interactive Streamlit operations dashboard
├── api.py                     # FastAPI server exposing REST endpoints
├── requirements.txt           # Python dependency specifications
├── .env.example               # Environment variables template
├── backend/                   # Core business logic, ML, and optimization
│   ├── config.py              # Centralized application settings & constants
│   ├── data/                  # Data models, schema validators & synthetic generator
│   │   ├── generator.py       # Deterministic realistic port operations data synthesizer
│   │   ├── loader.py          # Data ingestion, validation, and normalization
│   │   └── sample_data/       # Reference CSV datasets (vessels, berths, cranes, terminals)
│   ├── models/                # Machine learning & statistical congestion prediction
│   │   ├── features.py        # Temporal sliding window feature engineer
│   │   ├── congestion_model.py# ML Random Forest congestion risk scoring engine
│   │   └── hotspot_detector.py# Multi-terminal bottleneck & queue forecaster
│   ├── optimization/          # Prescriptive operations engine (Google OR-Tools CP-SAT)
│   │   ├── routing.py         # Dynamic proactive terminal rerouting recommender
│   │   ├── berth_optimizer.py # Mixed Integer Constraint Programming for Berth Allocation
│   │   └── crane_optimizer.py # Dynamic Crane Resource Assignment Engine
│   ├── planner/               # Operational plan generation & business metrics
│   │   ├── plan_generator.py  # 72-hour rolling operational schedule builder
│   │   └── metrics.py         # Baseline vs Optimized comparative KPI calculation
│   └── copilot/               # Conversational AI & Decision Intelligence
│       ├── explainability.py  # Transparent reasoning generation for recommendations
│       ├── scenario_simulator.py # Interactive What-If simulation engine
│       ├── prompts.py         # IBM Bob & watsonx prompt definitions
│       └── bob_agent.py       # Grounded conversational reasoning agent
└── tests/                     # Comprehensive test suite covering all modules
    ├── test_data_loader.py
    ├── test_congestion_model.py
    ├── test_optimization.py
    ├── test_planner.py
    ├── test_what_if.py
    └── test_copilot.py
```

## Running the Application
- **Interactive UI**: `streamlit run src/app.py`
- **Headless REST API**: `uvicorn src.api:app --reload --port 8000`
- **Unit & Integration Tests**: `pytest src/tests/ -v`
