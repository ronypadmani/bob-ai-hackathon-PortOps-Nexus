# Problem Statement — The $10B+ Global Port Congestion Crisis

## Executive Summary
Global supply chains run through maritime container ports. Over 80% of world merchandise trade by volume travels by sea. Yet modern container ports—managing multi-billion-dollar fleets, deep-water berths, ship-to-shore (STS) gantry cranes, and massive container yards—frequently operate with legacy, disconnected scheduling workflows and static spreadsheets.

During the catastrophic **2021 Los Angeles / Long Beach port congestion crisis**, over **100 ultra-large container vessels (ULCVs) were forced to anchor offshore for weeks**, unable to dock. This backlog triggered global supply chain gridlock, acute container shortages, and estimated economic damages exceeding **$10 Billion USD**.

---

## The Target Audience & Stakeholders
1. **Port Shift Supervisors & Terminal Operations Managers**: Responsible for assigning incoming vessels to physical berths and staging labor/stevedoring gangs across 8-hour and 24-hour shifts.
2. **Harbor Pilots & Vessel Traffic Services (VTS)**: Coordinating safe vessel navigation, inbound pilotage, and anchoring queues in harbor approaches.
3. **Container Terminal Operators (MTOs)**: Managing berth throughput, crane moves per hour (GMPH), and yard stack dwell times.
4. **Ocean Carriers & Logistics Alliances (e.g. 2M, Ocean Alliance, THE Alliance)**: Seeking reliable berth windows, minimum turnaround times, and fuel-efficient sailing speeds.

---

## Why Existing Systems Fail

### 1. Manual Spreadsheet Scheduling
Berth and crane allocation is traditionally conducted manually using legacy Terminal Operating Systems (TOS) and disconnected spreadsheets. These manual methods cannot mathematically evaluate the combinatorial complexity of dynamic vessel arrivals, variable container move counts, draft/length constraints, crane rail travel conflicts, and yard dwell saturation simultaneously.

### 2. Reactive Congestion Identification
Congestion hotspots are currently recognized **reactively**—after vessels have already entered harbor waters and formed offshore queues. At this juncture, demurrage penalties are already accumulating, harbor anchorages are saturated, and downstream intermodal rail connections are missed.

### 3. Late & Suboptimal Alternate Routing
When a terminal reaches capacity, harbor masters and vessel operators lack real-time predictive decision support to evaluate partner terminal capacities. Alternate routing decisions come too late or are rejected due to lack of transparent physical compatibility checks (draft, LOA, crane availability).

---

## Quantified Pain Points & Economic Cost

| Bottleneck Category | Traditional Operations | Impact / Cost |
| :--- | :--- | :--- |
| **Vessel Wait at Anchor** | 36 – 120+ hours per vessel call | $25,000 – $50,000 / day in vessel charter and demurrage costs |
| **Berth Allocation** | Static FIFO assignment in spreadsheets | 20–35% idle berth gaps between vessel calls |
| **Crane Gang Allocation** | Fixed 3-crane allocation regardless of TEU load | Suboptimal crane productivity; delayed turnarounds for critical cargo |
| **Emissions & Fuel Burn** | Auxiliary diesel generator burning at anchor | Hundreds of metric tons of avoidable CO₂ and PM2.5 harbor pollution |
| **Supply Chain Disruptions** | Unpredictable container discharge times | Missed intermodal rail slots, chassis shortages, and factory shutdowns |

---

## Why This Problem Matters Now
With rising global trade volumes, the adoption of Ultra Large Container Vessels (exceeding 20,000 TEU and 400m LOA), and intensifying climate pressures to decarbonize maritime corridors, port operators urgently require an intelligent, automated, and explainable **Port Operations Copilot**. 

By predicting congestion hotspots up to **72 hours in advance**, optimizing berth and crane assignments with **Google OR-Tools CP-SAT**, and proactively recommending alternate terminal routings, ports can systematically eliminate bottlenecks before a single ship queues offshore.
