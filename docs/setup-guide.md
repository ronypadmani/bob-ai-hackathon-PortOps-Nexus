# Setup & Reproduction Guide — Port Operations Copilot

This guide provides step-by-step instructions to install, configure, verify, and run the **Port Operations Copilot** from a clean environment.

---

## 1. Prerequisites
- **Python**: Version `3.10` or `3.11` (64-bit)
- **Git**: Installed and configured
- **Operating System**: Windows, Linux, or macOS

---

## 2. Clone the Repository & Setup Environment

```bash
# Clone the repository
git clone https://github.com/drijesh-ppatel/bob-ai-hackathon-portops-nexus.git
cd bob-ai-hackathon-portops-nexus

# Create a clean virtual environment
python -m venv .venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Windows (CMD):
.venv\Scripts\activate.bat
```

---

## 3. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r src/requirements.txt
```

---

## 4. Environment Variables Configuration

Copy `src/.env.example` to `src/.env` (or configure system environment variables):

```bash
# On Linux/macOS:
cp src/.env.example src/.env
# On Windows:
copy src\.env.example src\.env
```

### Environment Variables Reference

| Variable | Required? | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `APP_NAME` | No | `Port Operations Copilot` | Display name of the application |
| `PLANNING_HORIZON_HOURS` | No | `72` | Rolling planning horizon duration |
| `WATSONX_API_KEY` | Optional | `""` | IBM Cloud watsonx API key (fallback local engine active if omitted) |
| `WATSONX_PROJECT_ID` | Optional | `""` | IBM Cloud watsonx project ID |
| `WATSONX_URL` | Optional | `https://us-south.ml.cloud.ibm.com` | watsonx API endpoint URL |
| `WATSONX_MODEL_ID` | Optional | `ibm/granite-3-8b-instruct` | IBM Granite Foundation model ID |
| `ORTOOLS_SOLVER_TIME_LIMIT_SECONDS` | No | `30` | Maximum solve time for CP-SAT solver |

---

## 5. Verification: Running the Automated Test Suite

Run the full pytest suite to verify data loaders, ML models, OR-Tools optimization, 72-hour planners, and copilot agent:

```bash
pytest -v
```

Expected output:
```
======================== 14 passed in ~10s ========================
```

---

## 6. Running the Applications

### Option A: Interactive Streamlit Operations Dashboard (Recommended)

Launch the primary operations UI:
```bash
streamlit run src/app.py
```
Open your browser at `http://localhost:8501`.

### Option B: Headless FastAPI REST Server

Launch the REST API server:
```bash
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```
- Interactive Swagger API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

---

## 7. Troubleshooting Common Issues

| Error / Symptom | Root Cause | Solution |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'src'` | PYTHONPATH does not include root folder | Run commands from repository root where `pytest.ini` is located, or set `PYTHONPATH=.` |
| `ImportError: cannot import name 'ComplexWarning'` | Older scikit-learn version with NumPy 2.x | Run `pip install --upgrade scikit-learn` (version >= 1.4.0) |
| `Address already in use: port 8501` | Previous Streamlit instance still running | Run `streamlit run src/app.py --server.port 8502` |
| `OR-Tools Timeout` | Highly constrained custom dataset | Increase `ORTOOLS_SOLVER_TIME_LIMIT_SECONDS` in `.env` |
