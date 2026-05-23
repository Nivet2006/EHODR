# 🏥 Emergency Hospital Resource Optimizer (EHODR)

EHODR is a high-fidelity, decision-support dashboard and multi-solver optimization suite designed for real-time allocation of critical healthcare resources (ICU beds, ventilators, medical staff) during severe regional disasters. 

---

## 🚀 System Architecture

EHODR provides a unified interface built on Streamlit that translates triage severities and geographical distance matrices into optimized allocation vectors. It protects overloaded emergency rooms and routes critical patients to facilities best equipped to treat them.

```
                    ┌───────────────────────────────────┐
                    │  Emergency Dispatcher Dashboard  │
                    │       (Streamlit Interface)       │
                    └─────────────────┬─────────────────┘
                                      │ Configure Scenario & Solver
                                      ▼
                    ┌───────────────────────────────────┐
                    │    Multi-Solver Engine Core       │
                    └────┬────────────┬────────────┬────┘
                         │            │            │
                         ▼            ▼            ▼
             ┌───────────────┐ ┌──────────────┐ ┌──────────────┐
             │Exact Classical│ │  Simulated   │ │ Quantum QAOA │
             │ Combinatorial │ │  Annealing  │ │ Optimization │
             │  Brute Force  │ │  (Thermal)  │ │ (QUBO/Qiskit)│
             └───────────────┘ └──────────────┘ └──────────────┘
```

For a detailed breakdown of mathematical formulations, test scenarios, and project roadmap, see the [Reference Documentation](#-reference-documentation-hierarchy) section below.

---

## 📂 Project Directory Structure

This repository contains the following core files and configurations:

```text
EHODR/
├── app_enhanced.py           # Main Streamlit dashboard & core solver engines
│
├── Explainer.md              # Plain-language guide of core concepts & user controls
├── testing.md                # Interactive testing cases and diagnostic inputs
├── FUTURE.md                 # Technical engineering roadmap and scaling blueprint
│
├── run_dashboard.ps1         # PowerShell script shortcut to launch the app
├── run_dashboard.bat         # Windows CMD script shortcut to launch the app
├── kill_all.ps1              # PowerShell script shortcut to stop all active processes
└── kill_all.bat              # Windows CMD script shortcut to stop all active processes
```

---

## ⚙️ Core Solver Paradigms

EHODR implements three distinct algorithmic solver pathways inside [app_enhanced.py](file:///c:/codingprojects/EHODR/app_enhanced.py):

1. **Exact Classical Solver**: Exhaustively searches the entire combinatorial space to guarantee absolute mathematical optimality. Perfect for verifying smaller triage grids.
2. **Simulated Annealing (Quantum-Inspired)**: Uses statistical thermodynamic cooling via a custom physical state transitions class (`HospitalAllocationAnnealer`) to bypass local minima in high-dimensional solution spaces. Highly efficient for large-scale disaster scenarios.
3. **Quantum QAOA Solver**: Formulates allocations as a Quadratic Unconstrained Binary Optimization (QUBO) problem using Qiskit. Dynamically simulates parameterized quantum circuits under matching problem and mixer Hamiltonians.

> [!NOTE]
> **Streamlit Multi-Threaded Signal Patching**: Standard simulated annealing libraries try to register signal handlers for `SIGINT` on creation. Since Streamlit runs scripts in auxiliary background threads, this normally raises runtime errors. EHODR includes an active, thread-safe monkeypatch for `signal.signal` to handle transitions smoothly.

---

## 🎨 Key Features & Controls

* **📝 Triage Patient Registrar (New!)**:
  * An interactive intake form where operators register incoming arrivals in real-time by typing their name, age, transit distances, and selecting active symptoms (e.g. Altered Mental Status, Respiratory Distress).
  * Automatically calculates an **Emergency Severity Index (ESI 1-5)** priority score based on symptom profiles, translating them into solver severities.
  * *UAMS Agent Memory Sync*: Features an optional checkbox that connects to the `UniversalMemoryClient` in [memory_client.py](file:///c:/codingprojects/EHODR/agents/memory_client.py) to save registered patient profiles semantically in the vector database backend.
  * *Triage Registry Board*: Renders a beautiful visual table in the main panel to view the active queue, clear the pool, or remove individual patients.
* **Dynamic Disaster Presets**: Instantly load high-stress presets such as **Mass Casualty** (10 patients, 3 hospitals), **Pandemic Surge** (12 patients, 3 hospitals), **Earthquake** (8 patients, 2 hospitals), or choose **📝 Live Patient Registrar** to build an interactive triage pool.
* **Multi-Dimensional Constraint Safety**: Solvers guarantee that total allocated patients never exceed available **ICU Beds**, **Ventilators**, or **Emergency Medical Staff** per hospital.
* **Advanced Heuristics Engine**:
  * *Doctor Specialties*: Automatically routes life-threatening Severity 3 cases to the primary trauma center (**Hospital H1**).
  * *Transit Time Windows*: Scales objective penalty weights to prevent patients from being sent to hospitals outside safe geographical distance thresholds.
* **Visual Telemetry & Reporting**:
  * *Resource Load Visualizer*: Interactive bar charts comparing patient allocations against total hospital capacities.
  * *Distance Heatmap*: Color-coded grids mapping patient severity and hospital distance costs, dynamically rendering the registered patient names on the y-axis for granular dispatch tracking.
  * *CSV Export*: Direct local download button for finalized patient allocation directories containing actual names, ages, and symptoms.
* **🤖 Draggable EOC Command Advisor**:
  * An interactive client-side floating chatbot overlay widget that starts minimized as a beautiful pulsing bubble in the bottom-right corner.
  * Features native JavaScript dragging event listeners and minimization toggles that bypass Streamlit's backend reruns, persisting position coordinates in `sessionStorage`.
  * Integrated with an **Offline Fallback Diagnostic Analyzer** that automatically runs deterministic, rule-based diagnostic assessments of allocation tables, routing reasons, and saturation levels when local LLM services are offline.

---

## 🛠️ Quick Start & Local Development

### 1. Prerequisites
Ensure you have Python 3.10+ installed on your system.

### 2. Activate the Environment
Open a terminal in the project directory and activate the virtual environment:
```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Launch the Dashboard
You can start the dashboard in one of three ways:

* **Using PowerShell Shortcut (Recommended)**:
  ```powershell
  .\run_dashboard.ps1
  ```
* **Using Windows CMD / Double-Clicking**:
  ```cmd
  run_dashboard.bat
  ```
* **Using Streamlit CLI**:
  ```powershell
  .\venv\Scripts\streamlit run app_enhanced.py
  ```

Once running, the application will automatically launch at `http://localhost:8501` in your default browser.

### 4. Running Unit Tests
To execute the automated unit test suites:
```powershell
.\venv\Scripts\python -m pytest
```

### 5. Stopping the Dashboard
To shut down all active Streamlit and Python processes:
```powershell
# In PowerShell:
.\kill_all.ps1

# In Windows CMD:
kill_all.bat
```

---

## 📐 Mathematical Formulation

The optimization system maps hospital allocations to a Quadratic Unconstrained Binary Optimization (QUBO) Hamiltonian structure, where $x_{p,h} \in \{0,1\}$ denotes assigning patient $p$ to hospital $h$:

$$H = A \sum_{p} \left( \sum_{h} x_{p,h} - 1 \right)^2 + B \sum_{h} \text{Penalties}(x_{p,h}) + \sum_{p,h} (\text{Severity}_p \times \text{Distance}_{p,h}) x_{p,h}$$

* **Energy Objective (Term 3)**: Minimizes transit distance weighted by the severity of the patient's condition.
* **Allocation Constraint (Term A)**: Heavily penalizes invalid states where a patient is assigned to multiple or zero hospitals.
* **Capacity Constraint (Term B)**: Penalizes state spaces that violate physical capacities for ICU beds, ventilators, or medical staff.

---

## 📚 Reference Documentation Hierarchy

For more advanced inquiries, consult the comprehensive guides below:

1. **🏥 [Explainer.md](file:///c:/codingprojects/EHODR/Explainer.md) (User Orientation Guide)**: A non-technical breakdown explaining how severities, cost scores, and solvers calculate patient routing, with step-by-step instructions on reading results.
2. **🧪 [testing.md](file:///c:/codingprojects/EHODR/testing.md) (Interactive Testing Guide)**: Detailed test cases covering mass casualty constraints, pandemic ventilator bottlenecks, specialty routing, custom scenario feasibility failures, and the new **Patient Triage Registrar**.
3. **🚀 [FUTURE.md](file:///c:/codingprojects/EHODR/FUTURE.md) (Architectural Scaling Roadmap)**: Evolutionary plans for GIS real-world map integrations, multi-stage time-stepped simulation timelines, vehicle dispatch constraints (air-rescue vs ground), and physical IBM QPU hardware execution.
