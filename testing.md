# 🧪 EHODR Dashboard — Interactive Test Cases & Testing Guide


Viewed run_all.ps1:1-15
Viewed README.md:1-314

The EHODR platform provides several launch options depending on whether you want to run the full stack (with the Docker-based AI Memory System), the interactive live role dashboards, or the optimizer dashboard alone.

Here are the commands to run the different components from your PowerShell terminal in the `C:\codingprojects\EHODR` directory:

### 1. Launch the Full Stack (Recommended)
This command spins up the backend Docker containers (PostgreSQL, Qdrant, Redis, and the FastAPI Memory Gateway), installs dependencies, initializes databases, and launches the interactive Streamlit optimizer.
```powershell
.\run_all.ps1
```
* **Optimizer URL**: `http://localhost:8501`
* **Memory Gateway URL**: `http://localhost:8000`

---

### 2. Launch the Interactive HTML Command Dashboards (Role-based views)
This launches the live-ticking HTTP server for the role-specific dashboards (Ambulance, Guardian, and ER Command) along with the headless GIS optimizer engine.
```powershell
.\run_ehodr.ps1
```
*(Alternatively, you can delegate to the same launcher using `.\run_command_dashboards.ps1`)*
* **Main Hub Entry Point**: `http://127.0.0.1:8080/`
* **Ambulance cockpit**: `http://127.0.0.1:8080/ambulance.html`
* **Guardian portal**: `http://127.0.0.1:8080/guardian.html`
* **ER Command center**: `http://127.0.0.1:8080/er-command.html`

---

### 3. Launch Streamlit Optimizer Only (Bypass Docker backend)
If you do not have Docker running or wish to test only the quantum-inspired solver and Indian GIS map without the AI memory system, use:
```powershell
.\run_dashboard.ps1
```
* **Optimizer URL**: `http://localhost:8501`

---

### 4. Stop All Running Services
To clean up all active Python processes, Streamlit workers, and Docker containers when you are done:
```powershell
.\kill_all.ps1
```


This guide provides detailed, step-by-step test cases to run on the **Emergency Hospital Resource Optimizer (EHODR)** web dashboard. It shows you exactly what settings to configure, what data to enter, and what optimal outcomes to look for to verify the system.

1. Download & Install Docker Desktop
Go to the official Docker page: Download Docker Desktop for Windows.
Run the downloaded .exe installer.
During installation, make sure the option "Use WSL 2 instead of Hyper-V (recommended)" is checked.
Follow the prompt to complete the installation and restart your computer when requested.

docker --version
docker compose version

# In PowerShell:
.\run_all.ps1

# Or in Command Prompt:
run_all.bat

---

### 🛑 HOW TO KILL ALL PROCESSES:
If you want to stop the Streamlit frontend or shut down any active Docker containers, you can use these shortcuts:

* **Using PowerShell:**
  ```powershell
  .\kill_all.ps1
  ```
* **Using Windows Command Prompt / CMD:**
  ```cmd
  kill_all.bat
  ```
* **In the active terminal window:**
  Press `Ctrl + C` to stop the running process.




---
### HOW TO RUN APP LOCAL:

### SHORTCUT:

Viewed init_qdrant_collections.py:1-86
Edited run_all.ps1
Edited run_all.bat
Viewed testing.md:1-25
Edited testing.md

Yes! I have created **one-command runner scripts** specifically for your Windows setup that automate the entire process for you. 

These scripts will:
1. Spin up the Docker container stack in the background (`docker compose up -d`).
2. Wait a few seconds for database services to boot.
3. Automatically initialize the database and vector collections.
4. Launch the Streamlit Hospital Resource Optimizer frontend in your browser.

---

### How to Run Everything with 1 Command

#### 💻 In PowerShell:
```powershell
.\run_all.ps1
```

#### 🖥️ In Windows Command Prompt (`cmd`):
```cmd
run_all.bat
```
*(You can also simply **double-click** on the [run_all.bat](file:///c:/codingprojects/EHODR/run_all.bat) file in Windows File Explorer!)*

---

### Where It's Documented
I have also integrated these instructions directly into your [testing.md](file:///c:/codingprojects/EHODR/testing.md) file so you always have a quick reference.

---

### Manual Step-by-Step Execution

#### ⚡ Option A: Run Everything with 1 Command (Recommended)
We created a helper script that automatically spins up Docker containers, initializes the database vector collection, and launches the Streamlit frontend.

* **Using PowerShell:**
  ```powershell
  .\run_all.ps1
  ```
* **Using Windows Command Prompt / Double-Clicking:**
  ```cmd
  run_all.bat
  ```

---

#### 🛠️ Option B: Manual Step-by-Step Execution
If you want to run specific parts of the application individually:

### 1. Run the Hospital Resource Optimizer Dashboard (Streamlit Frontend)
To launch the interactive web interface (where you can run simulated annealing, classical, and quantum QAOA solvers):

```powershell
.\venv\Scripts\streamlit run app_enhanced.py
```
*(Once run, this will automatically open `http://localhost:8501` in your browser).*

---

### 2. Start the Universal AI Memory System (Gateway & DB Backend)
If you want to spin up the long-term memory backend (FastAPI, Qdrant, PostgreSQL, and Redis) using Docker Compose:

* **To start the services:**
  ```powershell
  docker compose up -d
  ```
* **To initialize the databases & vector collections:**
  ```powershell
  .\venv\Scripts\python scripts/init_qdrant_collections.py
  ```
* **To stop the services:**
  ```powershell
  docker compose down
  ```

---

### 3. Run the Unit Test Suite
To run the automated tests and verify the code is fully operational:

```powershell
.\venv\Scripts\python -m pytest
```

----

## 📋 Quick Reference: How to input settings in the dashboard
1. **The Sidebar** (on the left) is where you select your scenario, adjust resources, check heuristic rules, and choose your solver.
2. **The Run Button** (at the bottom of the sidebar) triggers the calculations.
3. **The Tabs** (in the main screen area) display the results under:
   * **Allocation Results** (Tables and metrics)
   * **Visualization Dashboard** (Charts and heatmaps)
   * **Quantum Formulation** (Math formulas and circuit blueprints)

---

## 🎯 Curated Test Cases

### 🛠️ Test Case 1: Mass Casualty (High-Stress Regional Routing)
* **Objective**: Verify that the system can handle a high patient volume and route them efficiently without exceeding limited ICU bed space.
* **What to enter in the sidebar**:
  1. **Load disaster scenario preset**: Choose `Mass Casualty (10 patients)`.
  2. **Advanced Heuristic Rules**: Leave both options **unchecked**.
  3. **Active optimization algorithm**: Choose `Simulated Annealing (Quantum‑Inspired)` or `Exact Classical (Brute Force)`.
  4. **Run**: Click `🚀 Execute Optimization Run`.
* **What to look for in the results**:
  * **Status**: You should see a green box: `🎉 Optimization Run Completed`.
  * **Cost Score**: 
    * If using **Exact Classical**: Look for a **Total Severity-Distance Cost Score** of exactly **135.00**.
    * If using **Simulated Annealing**: Look for a cost score of **135.00** (optimal global minimum) or a near-optimal score like **149.00** (depending on stochastic search state convergence).
  * **Allocation Results Tab (Exact Classical)**:
    * Check the **Hospital Capacities & Utilization** table.
    * Verify that **Hospital H1** has exactly **4** patients, **H2** has exactly **4** patients, and **H3** has exactly **2** patients allocated. None of these exceed the available ICU beds, vents, or staff limits.
  * **Visualization Dashboard Tab**:
    * View the **Bed Allocation vs Capacity** bar chart. Notice the dark blue allocation bars are strictly below or equal to the yellow total capacity bars.

---

### 💨 Test Case 2: Pandemic Surge (Ventilator Bottleneck)
* **Objective**: Test the system's ability to distribute patients safely when breathing equipment (ventilators) is highly constrained.
* **What to enter in the sidebar**:
  1. **Load disaster scenario preset**: Choose `Pandemic Surge (12 patients)`.
  2. **Advanced Heuristic Rules**: Leave both options **unchecked**.
  3. **Active optimization algorithm**: Choose `Exact Classical (Brute Force)`.
  4. **Run**: Click `🚀 Execute Optimization Run`.
* **What to look for in the results**:
  * **Status**: Green completion box.
  * **Cost Score**: Look for an optimal **Total Severity-Distance Cost Score** of exactly **139.00**.
  * **Allocation Results Tab**:
    * Check the **Hospital Capacities & Utilization** table.
    * Verify that **H1** has exactly **4** allocations, **H2** has **5** allocations, and **H3** has **3** allocations.
    * H3 has hit its hard limit of 3 Emergency Medical Staff, preventing any further allocations and forcing other patients to H1 and H2.

---

### 🚨 Test Case 3: Specialty Heuristics (Trauma Center Routing)
* **Objective**: Verify that the advanced rule successfully routes all critical patients (Severity level 3) to the primary trauma center (**Hospital H1**).
* **What to enter in the sidebar**:
  1. **Load disaster scenario preset**: Choose `Earthquake (8 patients)`.
  2. **Advanced Heuristic Rules**: **Check** the box `Enforce doctor specialties (trauma vs pediatric)`.
  3. **Active optimization algorithm**: Choose `Exact Classical (Brute Force)`.
  4. **Run**: Click `🚀 Execute Optimization Run`.
* **What to look for in the results**:
  * **Status**: Green completion box.
  * **Cost Score**: Look for an optimal **Total Severity-Distance Cost Score** of exactly **173.00**.
  * **Allocation Results Tab**:
    * Look at the **Patient Allocation Directory** table.
    * Find patients with **Severity Level 3** (such as `Patient-1`, `Patient-3`, `Patient-4`, and `Patient-7`).
    * Check their **Assigned Unit** column. **Every patient with Severity Level 3 MUST be routed to H1** because of the trauma center specialization rule.
    * Look at the remaining stable patients (Severity 1 or 2). They are routed to **H2** to balance capacity.

---

### 🛠️ Test Case 4: Creating a Custom Scenario (Your Own Custom Settings)
* **Objective**: Design your own custom event to test a specific constraint balance.
* **What to enter in the sidebar**:
  1. **Load disaster scenario preset**: Choose `Custom`.
  2. **Number of emergency patients**: Set the slider to `6`.
  3. **Number of hospitals in network**: Set the slider to `2`.
  4. **Hospital H1 Capacities**:
     * ICU Beds: `3`
     * Vents: `3`
     * Staff: `3`
  5. **Hospital H2 Capacities**:
     * ICU Beds: `3`
     * Vents: `3`
     * Staff: `3`
  6. **Advanced Heuristic Rules**: Leave **unchecked**.
  7. **Active optimization algorithm**: Choose `Exact Classical (Brute Force)`.
  8. **Run**: Click `🚀 Execute Optimization Run`.
* **What to look for in the results**:
  * **Status**: Green completion box.
  * **Cost Score**: Look for a **Total Severity-Distance Cost Score** of exactly **60.00**.
  * **Allocation Results Tab**:
    * Check the **Hospital Capacities & Utilization** table.
    * Verify that the 6 patients are perfectly divided: exactly **3** routed to **H1** and exactly **3** routed to **H2**.
    * Since beds are capped at 3 per hospital, the optimizer balanced the load perfectly, utilizing 100% of both hospitals' space without overflowing.

---

### ⚠️ Test Case 5: Triage Limit & Feasibility Failure Test
* **Objective**: Verify that the app catches situations where there are more patients than total hospital resources and warns the user gracefully instead of crashing.
* **What to enter in the sidebar**:
  1. **Load disaster scenario preset**: Choose `Custom`.
  2. **Number of emergency patients**: Set the slider to `12` (Maximum patients).
  3. **Number of hospitals in network**: Set the slider to `2`.
  4. **Hospital H1 Capacities**:
     * ICU Beds: `2` (Extremely low capacity)
     * Vents: `2`
     * Staff: `2`
  5. **Hospital H2 Capacities**:
     * ICU Beds: `2` (Extremely low capacity)
     * Vents: `2`
     * Staff: `2`
  6. **Active optimization algorithm**: Choose `Exact Classical (Brute Force)`.
  7. **Run**: Click `🚀 Execute Optimization Run`.
* **What to look for in the results**:
  * **Status**: You should see a red error box:
    `❌ Feasible Allocation Error: The resource constraints are too tight for the given scenario. No feasible solution exists classical or quantum.`
  * **Helpful Guidance**: Below the error, an info box should suggest:
    `💡 Action: Try increasing beds or staff capacity in the sidebar, or lowering the patient count.`
  * This confirms the safety barriers are working flawlessly!

---

### 📝 Test Case 6: Live Patient Triage Registrar (Real-time Operations)
* **Objective**: Verify that operators can dynamically register incoming patient profiles, automatically assign ESI severity levels, optionally sync them to UAMS Agent Memory, and execute optimization runs using their real profiles.
* **What to enter in the sidebar**:
  1. **Load disaster scenario preset**: Choose `📝 Live Patient Registrar`.
  2. Notice that the **Active Emergency Patient Registry** displays a default list of 6 realistic patients (e.g., John Doe, Jane Smith, Bob Johnson) with their ages, symptoms, and automatic ESI triage priorities.
  3. **Patient Intake Form** (under sidebar):
     * Patient Name: Enter `Victoria Sterling`
     * Patient Age: Enter `42`
     * Symptoms: Select `Respiratory Distress / Difficulty Breathing` and `Severe Trauma / Lacerations`
     * Transit Distances: To H1 = `3`, To H2 = `12`, To H3 = `18`
     * Sync with UAMS Agent Memory: **Check** this box (if the UAMS gateway is active).
  4. Click `➕ Register Patient`.
* **What to look for in the results**:
  * The registrar pool automatically updates to **7 patients** in the registry table.
  * `Victoria Sterling` appears in the table with priority `ESI 2` (Severity 3 - Critical) and distances `3, 12, 18`.
  * If the UAMS gateway is active, a green success message confirms: `Saved to Agent Memory` along with the persisted memory ID.
  * **Run**: Select `Simulated Annealing` or `Exact Classical` and click `🚀 Execute Optimization Run`.
  * **Allocation Results Tab**:
    * View the **Patient Allocation Directory** table. Note that the entries now display the patients' actual names (including `Victoria Sterling`), ages, and physical symptoms instead of placeholder Patient IDs!
    * Review the assigned units to ensure capacities are preserved.
  * **Visualization Dashboard Tab**:
    * Hover over the **Distance Heatmap**. The y-axis labels now dynamically render the first 10 characters of the patients' registered names (e.g., `Victoria S`) for high-fidelity operations telemetry!

---

## 📈 Designing your own Test Cases

When creating your own test scenarios, remember these basic rules:
1. **The Capacity Check**: Ensure the sum of all hospital beds is **greater than or equal to** the total number of patients:
   $$\sum \text{Beds} \ge \text{Patients}$$
   If this is not true, the scenario is physically impossible to solve (which triggers the **Feasibility Error** from Test Case 5).
2. **Heuristic Constraints**: Checking `Enforce doctor specialties` places a heavy burden on **H1** (since all critical cases must go there). If H1's bed capacity is lower than the number of Severity 3 patients, the scenario will be impossible to solve. Always give H1 generous bed space when using this rule!
