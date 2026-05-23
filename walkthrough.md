# Walkthrough: Emergency Hospital Resource Optimizer (EHODR) Dashboard

This walkthrough covers the architecture, features, and deployment of the **Emergency Hospital Resource Optimizer (EHODR) Streamlit Application**—a high-fidelity solver dashboard for real-time allocation of critical healthcare resources (beds, ventilators, medical staff) during extreme disaster scenarios.

---

## 🛠️ Summary of Accomplishments

All major development and integration objectives have been achieved, verified, and compiled with zero configuration drift:

### 1. Robust Environment & Packages
- Installed all heavy scientific computing libraries inside the Python virtual environment: `streamlit`, `numpy`, `pandas`, `matplotlib`, `seaborn`, `simanneal`, `qiskit`, and `qiskit-optimization` (along with compiling `docplex`).
- Verified all environment imports with zero failures.

### 2. Multi-Solver Paradigm
Implemented three distinct algorithmic solver pathways inside [app_enhanced.py](file:///c:/codingprojects/EHODR/app_enhanced.py):
- **Exact Classical Solver**: Exhaustively searches the full combinatorial space to guarantee absolute mathematical optimality.
- **Simulated Annealing (Quantum-Inspired)**: Uses statistical thermodynamic cooling via a custom physical state transitions class (`HospitalAllocationAnnealer`) to bypass local minima in high-dimensional solution spaces.
- **Quantum QAOA Solver**: Formulates allocations as a Quadratic Unconstrained Binary Optimization (QUBO) problem using Qiskit. Dynamically evolves qubit systems under matching problem and mixer Hamiltonians.

### 3. Dynamic Disaster Presets & Constraints
- Added support for quick loading of standard disaster scenarios:
  - **Mass Casualty**: 10 patients across 3 hospitals.
  - **Pandemic Surge**: 12 patients across 3 hospitals.
  - **Earthquake**: 8 patients across 2 hospitals.
- Integrated customizable multi-dimensional constraints (beds, ventilators, and emergency medical staff capacities).
- Added advanced heuristic rules:
  - **Doctor Specialties**: Trauma or pediatric specializations routing critical patients to H1 automatically.
  - **Transit time windows**: Scaled penalty ceilings for high-distance pathways.

### 4. Interactive Visualizations & Reporting
- Heatmaps mapping severity and hospital distance costs dynamically.
- Resource utilization bar charts showing patient allocations against total hospital capacities.
- Mathematical Hamiltonian LaTeX formulation explanation.
- Real-time progress tracker checkboxes mapping out solution state transitions.
- High-performance CSV export to save optimized allocations locally.

### 5. Streamlit Multi-Threading & Thread-Safe Signal Patching
- **Issue**: Standard `simanneal` constructor tries to register a signal handler for `SIGINT` on creation. Since Streamlit runs scripts in auxiliary background threads instead of Python's main thread, calling `signal.signal` raises `ValueError: signal only works in main thread of the main interpreter`.
- **Resolution**: Designed and implemented a global monkeypatch for `signal.signal` at the top of [app_enhanced.py](file:///c:/codingprojects/EHODR/app_enhanced.py) that catches the `ValueError` and falls back gracefully when running in auxiliary threads, enabling robust thread-safe Simulated Annealing execution.

### 6. Draggable Floating Pop-Up EOC Chatbot
- **Innovative Client-Side Overlay**: Refactored the dashboard from a split screen to a gorgeous 100% full-width layout, maximizing the visibility of charts and tables, while floating the **🤖 EOC Advisor Chatbot** as a premium pop-up overlay widget in the bottom-right corner.
- **Dynamic Minimization & Expansion (Fixed & Refactored)**: The chatbot starts minimized as a beautiful, pulsing circular bubble with the `"🤖"` icon. Clicking it expands it smoothly without triggering Streamlit backend reruns. Clicks are guaranteed to be captured by overriding interactive overlays with `pointer-events: auto !important` and applying native inline `onclick` triggers to bypass React DOM replacement.
- **Robust Client-Side Dragging**: Added native JavaScript event listeners (`mousedown`, `mousemove`, `mouseup`) allowing operators to grab and drag the header (`🤖 EOC Advisor`) to any position on the screen.
- **Browser-State Persistence**: Leveraged browser `sessionStorage` to save dragging coordinates and minimization state, ensuring the chatbot maintains its layout and toggled state across execution reruns and user inputs.
- **Offline Fallback Diagnostic Analyzer**: Integrated a connection status badge (`● Connection Active` / `● Heuristic Fallback` / `● Advisor Standby`) that automatically falls back to an intelligent rule-based diagnostic engine if local Ollama models are offline.

### 7. Live Patient Intake Registrar & Triage Form (New!)
- **Dynamic Patient Registry**: Added a dedicated `📝 Live Patient Registrar` preset that loads a list of realistic default patients and provides a visual interactive board in the main panel to manage, clear, and remove active triage cases.
- **Tabular Intake & ESI Scoring**: Created a clean registrar form in the sidebar where operators register patients by name, age, symptoms, and specific transit distances. The engine dynamically calculates an Emergency Severity Index (ESI 1-5) and maps it to solver severity levels (1-3).
- **Universal Agent Memory Sync Integration**: Built a robust sync checkbox that integrates directly with `UniversalMemoryClient` from [memory_client.py](file:///c:/codingprojects/EHODR/agents/memory_client.py) to save registered patient profiles semantically in the vector database backend when selected.
- **Dynamic Telemetry & Visuals**: Configured the allocation directories to display registered names, ages, and symptoms in results tables, and dynamically injected patient names onto the y-axis of the Distance Heatmap.

---

## 📐 Mathematical Formulation

The optimization system maps resource allocations to a Quadratic Unconstrained Binary Optimization (QUBO) Hamiltonian structure, where $x_{p,h} \in \{0,1\}$ denotes allocating patient $p$ to hospital $h$:

$$H = A \sum_{p} \left( \sum_{h} x_{p,h} - 1 \right)^2 + B \sum_{h} \text{Penalties}(x_{p,h}) + \sum_{p,h} (\text{Severity}_p \times \text{Distance}_{p,h}) x_{p,h}$$

- **Energy Objective (Term 3)**: Minimizes the distance traveled weighted by the severity of the patient's condition.
- **Allocation Constraint (Term A)**: Strongly penalizes invalid allocations where a patient is assigned to multiple or zero hospitals.
- **Capacity Constraint (Term B)**: Penalizes state spaces that violate hard hospital capacities for beds, ventilators, or medical staff.

---

## 🚀 How to Launch and Test

To launch the interactive dashboard locally:

1. **Activate the Virtual Environment & Launch Streamlit**:
   Run the following command in your PowerShell terminal to boot up the application server:
   ```powershell
   .\venv\Scripts\streamlit.exe run app_enhanced.py
   ```

2. **Select an Emergency Preset**:
   Use the left-hand sidebar to choose a preset scenario (e.g., **Mass Casualty (10 patients)**) or toggle "Custom" to set manual constraints and patient distributions.

3. **Choose an Optimization Algorithm**:
   - For rapid physical state transitions, select **Simulated Annealing**.
   - For complete combinatorial verification, select **Exact Classical**.
   - For standard parameterized quantum simulation, select **QAOA (Quantum)**.

4. **Execute Optimization**:
   Click **Execute Optimization Run** in the sidebar. The results will load in three comprehensive tabs:
   - **Allocation Results**: Patient directory, capacity metrics, and a direct **CSV Download** button.
   - **Visualization Dashboard**: Dual-axis capacity utilization charts and distance heatmaps.
   - **Quantum Formulation**: Interactive LaTeX equations and simulated QAOA circuit layouts.

> [!TIP]
> **Qiskit Version Resiliency (Resolved Compat Issues)**: The application includes a multi-layered import fallback layer designed for modern Qiskit (v1.0+ / v2.x) and legacy versions. We resolved compatibility errors regarding the removal of `qiskit.algorithms` in newer versions by:
> 1. Installing `qiskit-algorithms` (as of v1.0+, Qiskit's algorithms are located in this standalone package).
> 2. Dynamically importing `StatevectorSampler` (BaseSamplerV2) in modern environments as the standard `Sampler` reference primitive.
> 3. Integrating the `COBYLA` optimizer as a required explicit input parameter for the modern QAOA constructor.
> This makes the QAOA optimization pathway highly robust and future-proof across Qiskit releases.

> [!NOTE]
> **Feasibility Fallbacks**: If constraints are too tight (e.g., more patients than total hospital beds), the application catches the allocation failure gracefully and guides you to adjust sidebar parameters.
