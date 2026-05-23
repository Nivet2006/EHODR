# 🚀 Visionary Engineering Roadmap: Future of EHODR

This document outlines the evolutionary architectural roadmap for the **Emergency Hospital Resource Optimizer (EHODR)**. It covers advanced feature integrations, real quantum hardware routing, geographic dispatch, time-stepped simulation engines, and IoT infrastructure integration to transition the platform into an enterprise-grade disaster command suite.

---

## 🗺️ Architectural Phase Map

```mermaid
graph TD
    A[Current EHODR Dashboard] --> B[Phase 1: Geographic & Time-Stepped dispatch]
    A --> C[Phase 2: Dynamic AI Command Center]
    B --> D[Phase 3: Hybrid Classical-Quantum Core]
    C --> D
    D --> E[Phase 4: Real QPU Hardware Execution & IoT Sensors]
```

---

## 🤖 Phase 1: Real-Time AI Dispatch & Coordinator Chatbot

### A. Local Ollama Integration
* **Objective**: Introduce an interactive conversational interface that acts as an "Emergency Operations Center (EOC) Command Advisor."
* **Technical Specification**:
  * Utilize the local Ollama API gateway (already initialized in UAMS) to run open-weight models (e.g., `Llama-3-8B` or `Mistral-7B`) offline.
  * Dynamically extract active allocation tables, distance matrices, and capacity metrics from the Streamlit session state and inject them as context into the LLM system prompt.
* **Core Capabilities**:
  * **Allocation Reasoning**: Explain *why* a specific patient was routed to a farther hospital (e.g., *"Patient-3 is critical but was routed to H2 because Hospital H1’s ICU beds are currently 100% saturated"*).
  * **Resource Warning**: Alert operators of active system bottlenecks (e.g., *"Warning: Regional Medical Staff is at 92% utilization; any further critical incoming cases will trigger triage delays"*).

---

## 🗺️ Phase 2: GIS Real-World Interactive Mapping

### A. Geocoded Spatial Routing
* **Objective**: Transition from abstract distance matrices to real-world GIS coordinates.
* **Technical Specification**:
  * Integrate `folium` and `streamlit-folium` to display interactive spatial maps.
  * Map real hospital coordinates and generate mock patient pickup locations within a selectable metropolitan area (e.g., Seattle, New York, or London).
  * Use open routing APIs (like OpenStreetMap/OSRM) to calculate actual travel time profiles instead of linear Euclidean distances.
* **Visual Telemetry**:
  * **Hospital Nodes**: Displayed as dynamic pins. Green pins represent low occupancy, turning orange and blinking red as they hit 90%+ saturation.
  * **Patient Nodes**: Represented by color-coded circles matching their triage severity levels (Red = Severity 3, Yellow = 2, Green = 1).
  * **Dispatch Paths**: Draws active polyline paths mapping patients from coordinate origins to assigned hospital hubs in real-time.

---

## ⏰ Phase 3: Multi-Stage Time-Stepped Simulation

### A. 24-Hour Continuous Emergency Timeline
* **Objective**: Evolve the optimizer from a single static snapshot into a continuous time-series simulation.
* **Technical Specification**:
  * Divide the optimization horizon into discrete time blocks (e.g., 10-minute intervals over a 24-hour cycle).
  * Patients arrive dynamically based on an adjustable casualty curve (e.g., normal or Poisson distribution representing peak disaster arrivals).
  * Hospitals slowly treat and discharge minor patients over time, freeing up beds.
  * **Dynamic Re-Optimization**: Run the Simulated Annealing or classical solver at every time step to re-triage incoming cases, showing a live timeline playback of fluctuating capacities.

---

## 🚑 Phase 4: Multi-Modal Transport Dispatch

### A. Vehicle Asset Management
* **Objective**: Include vehicle limitations in the mathematical optimization constraints.
* **Vehicle Classes**:
  * **Standard Ambulances**: Plentiful, but travel slowly along ground routes (high distance cost penalty).
  * **Air-Rescue Helicopters**: Extremely fast, bypassing road blockages (zero distance penalty), but extremely limited in quantity.
* **QUBO Mathematical Extension**:
  * Expand the binary decision variable from $x_{p,h}$ (patient $p$ to hospital $h$) to $x_{p,h,v}$ where $v \in \{Ambulance, Helicopter\}$.
  * Incorporate vehicle availability constraints:
    $$\sum_{p,h} x_{p,h,Helicopter} \le \text{Total Helicopters}$$

---

## ⛈️ Phase 5: Environmental & Disaster Road Blockages

### A. Dynamic Terrain Routing Risks
* **Objective**: Simulate severe weather or physical terrain blockages that disrupt transportation networks.
* **Interactive Sliders**:
  * Add a **Disruption Severity** slider (Clear, Severe Flooding, Seismic Damage, Road Obstructions).
* **The Impact**:
  * Selecting "Severe Flooding" marks specific routes or coordinate zones on the map as "Blocked."
  * The system dynamically recalculates the distance matrix, scaling blocked pathways to infinity ($\infty$) and forcing the solvers to route patients through safe bypass roads to other hospitals.

---

## 🌀 Phase 6: Deeper Quantum Control Panel (The Ansatz Lab)

### A. Qiskit Solver Parameter Customizer
* **Objective**: Provide quantum developers and judges with low-level parameter tuning capabilities.
* **Parameter Controls**:
  * **Classical Minimizers**: Let users choose the classical optimizer used by Qiskit to tune the parameterized quantum gates (e.g., `COBYLA`, `SLSQP`, `SPSA`, or `Nelder-Mead`).
  * **Ansatz Layers (Reps)**: Increase layers to observe quantum state convergence profiles.
  * **Quantum Mixer Hamiltonians**: Toggle between standard $X$-Mixers and complex $XY$-Mixers to verify search space constraints.
  * **Noise Simulation Engine**: Add a toggle to simulate real hardware gate errors, illustrating how the algorithm performs on imperfect, real-world NISQ (Noisy Intermediate-Scale Quantum) devices.

---

## 🔌 Phase 7: Real Physical Quantum Hardware Execution

### A. IBM Quantum Hub Integration
* **Objective**: Evolve the quantum solver from classical simulators to real, physical superconducting quantum computers.
* **Technical Specification**:
  * Integrate Qiskit Runtime Services (`qiskit-ibm-runtime`).
  * Add a secure API key field in the sidebar to let users authenticate their IBM Quantum accounts.
  * Add a **Target Hardware** dropdown to select active IBM QPUs (e.g., `ibm_brisbane`, `ibm_kyoto`).
* **Visual Telemetry**:
  * When executing, display real-time physical QPU queue wait times, active job IDs, and physical read-out error mitigation parameters.
  * Display a side-by-side comparison of Simulators vs. Real Hardware Cost accuracy.

---

## 📡 Phase 8: IoT Sensor Real-Time Capacity Sync

### A. Automated Resource Tracking
* **Objective**: Eliminate manual input sliders and synchronize hospital resources in real-time.
* **Technical Specification**:
  * Connect the Streamlit dashboard to a real-time database (e.g., Supabase or PostgreSQL) linked to smart IoT medical equipment.
  * **IoT Smart Beds**: Automatically update regional bed counts as physical pressure-sensor pads on beds register a patient.
  * **IoT Ventilator Status**: Automatically decrement ventilator availability the moment an active mechanical breathing loop is initiated in an ICU ward.
  * This creates a fully automated, hands-free regional dispatch coordinator.
