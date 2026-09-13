# Solution Overview — Port Operations Copilot

## Conceptual Architecture & Core Mechanisms
**Port Operations Copilot** is a closed-loop prescriptive decision intelligence platform designed to replace manual spreadsheet scheduling with predictive machine learning and exact mathematical optimization.

```
+-----------------------------------------------------------------------------------+
|                            PORT OPERATIONS COPILOT                                |
|                                                                                   |
|  [ Ingest & Validate ] --> [ Sliding-Window ML ] --> [ Proactive Rerouting ]     |
|   Vessel Schedules,         Congestion Risk (0-100)    Feasibility & Impact Check |
|   Berths, Cranes, Yards     Hotspot Detection          to Balance Port Terminals  |
|                                                              |                    |
|                                                              v                    |
|  [ 72h Master Plan ]  <-- [ Dynamic Cranes ]   <-- [ OR-Tools CP-SAT BAP ]        |
|   Gantt & Disruption       2-5 STS Gantry Cranes      Non-Overlapping Intervals,  |
|   What-If Studio           Workload Acceleration      Priority-Weighted Waiting   |
|            |                                                                      |
|            v                                                                      |
|  [ IBM Bob Copilot ]  --> Grounded Natural Language Operational Q&A + Audit Cards|
+-----------------------------------------------------------------------------------+
```

---

## 1. Data Ingestion & Validation
The system ingests and validates four core operational datasets:
- **`vessels.csv`**: Inbound vessel calls across a 72-hour planning horizon with ETAs, container moves, TEU volumes, vessel dimensions (LOA, draft), priority rankings (`CRITICAL`, `HIGH`, `NORMAL`, `LOW`), and preferred terminals.
- **`berths.csv`**: Deepwater and standard container berths across multiple terminals with length limits, draft depths, and availability clocks.
- **`cranes.csv`**: Ship-to-shore (STS) gantry cranes with moves/hour capacity, operational status, and maintenance windows.
- **`terminals.csv`**: Multi-terminal configuration with yard capacities, live utilization levels, and rail intermodal connectivity.

---

## 2. Machine Learning Congestion Predictor & Hotspot Detector
Rather than waiting for queues to accumulate, the system computes temporal demand-to-capacity metrics across 1-hour sliding time steps:
- **Berth Pressure Ratio**: Active in-window vessel count divided by available active berths.
- **Crane Workload Pressure**: Required container moves per hour versus gross operational crane rate.
- **Yard Saturation Index**: Projected yard TEU accumulation relative to terminal maximum capacity.

An ensemble **Random Forest Classifier** and **Gradient Boosting Regressor** score each hourly terminal state from 0 to 100 (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). Contiguous high-risk windows are grouped into **Hotspots** tagged with root-cause diagnostics (e.g. *Berth Overbooking*, *Yard Saturation*, *Crane Deficit*).

---

## 3. Prescriptive Google OR-Tools CP-SAT Optimization Engine
The Berth Allocation Problem (BAP) is formulated as an exact Constraint Programming model using Google OR-Tools `CpModel`:

$$\min \sum_{i=1}^N W_i \cdot (S_i - A_i) + \sum_{i=1}^N \sum_{b \in B_i} P_{i,b} \cdot x_{i,b}$$

Subject to:
1. **Arrival Precedence**: $S_i \ge A_i$ (Vessel cannot berth before its physical ETA).
2. **Berth Exclusivity**: `AddNoOverlap` over 2D space-time interval variables $I_{i,b} = [S_i, S_i + D_i]$ for all vessels assigned to berth $b$.
3. **Physical Feasibility**: Vessel length $\text{LOA}_i \le \text{MaxLen}_b$ and draft $\text{Draft}_i \le \text{MaxDraft}_b$.
4. **Dynamic Crane Allocation**: High-priority and ultra-large vessels are allocated up to 5 cranes to accelerate turnarounds:
$$D_i = \frac{\text{Containers}_i}{k \cdot \text{GMPH} \cdot \eta(k)}$$

---

## 4. Proactive Alternate Terminal Rerouting
When a terminal is predicted to enter a severe bottleneck (e.g. Terminal T2 reaching >80/100 risk during an arrival surge), the engine evaluates partner terminals:
1. Verifies physical draft and length constraints.
2. Checks available berth windows and yard headroom.
3. Computes estimated turnaround savings.
4. Generates a clear rerouting recommendation before the ship reaches harbor waters.

---

## 5. 6-Point Transparent Decision Explainability
Every recommendation is accompanied by an auditable 6-point explanation card:
1. **What happened?**
2. **Why is this a problem?**
3. **What does the system predict?**
4. **What action is recommended?**
5. **Why was this action selected?**
6. **What constraints influenced the decision?**

---

## 6. Conversational IBM Bob Copilot
Embedded inside the Streamlit dashboard, the IBM Bob Copilot provides conversational operational intelligence. It can be queried via natural language for immediate answers grounded strictly in live system state, backed by watsonx.ai Granite 3.0 prompt orchestration.
