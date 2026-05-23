# 🏥 Emergency Hospital Resource Optimizer (EHODR) — Simple Explainer Guide

Welcome! This friendly guide explains what the **Emergency Hospital Resource Optimizer** does, how it works in plain language, and how you can use it.

---

## 🌟 1. What does this app actually do?

Imagine an earthquake or a major pandemic has just happened. Dozens of injured patients need to go to a hospital.
* Some patients are in critical condition; others have minor injuries.
* Some hospitals are close by; others are far away.
* Every hospital has a limited number of **ICU beds**, **ventilators**, and **doctors**.

If all patients are sent to the closest hospital, it will immediately overflow, and people who need urgent care might not get a bed.

**This app is a super-smart digital dispatcher.** It instantly calculates the absolute best hospital for every single patient so that:
1. Critical patients get sent to the closest hospital that has open beds and equipment.
2. Minor patients are routed to other nearby hospitals with space.
3. No hospital is overloaded beyond its capacity.

---

## 🧭 2. Explaining the Core Ideas (No jargon!)

Here is how the app thinks about the problem:

* **Severity Level**: Patients are rated from **1** (minor scratches) to **3** (life-threatening/critical).
* **Cost Score**: The app calculates a "score" for every trip. A critical patient traveling a long distance has a very high "cost" (bad). The app's main goal is to keep this **Cost Score as low as possible** (good). It naturally prioritizes sending the most severely injured people to the nearest hospitals.
* **Resources**: The app makes sure that the number of assigned patients never exceeds the hospital's available **Beds**, **Ventilators**, or **Doctors**.

---

## ⚙️ 3. A Tour of the Sidebar Controls

When you open the app, you will see a settings panel on the left. Here is what you can adjust:

### 🎒 Load Disaster Presets
Instead of typing in details manually, you can load a scenario instantly:
* **Mass Casualty**: 10 patients and 3 hospitals. A high-stress test with lots of patients and few beds.
* **Pandemic Surge**: 12 patients and 3 hospitals. A scenario where breathing equipment (ventilators) is highly limited.
* **Earthquake**: 8 patients and 2 hospitals. Focused on rapid routing to nearby trauma centers.
* **Custom**: Create your own scenario! You can choose how many patients there are, how many hospitals, and set exactly how many beds/ventilators/doctors each hospital has.

### 🧠 Advanced Rules (Heuristics)
* **Enforce doctor specialties**: If checked, critical patients (Severity 3) are automatically forced to go to **Hospital H1** (which has the best trauma specialists).
* **Limit transfer windows**: If checked, the app prevents patients from being sent to hospitals that are too far away (distance greater than 15 units).

### 🤖 The Solver Engines (The Brains)
You can choose which math engine solves the problem:
1. **Exact Classical**: Checks every single possible combination. It is guaranteed to find the perfect, 100% correct solution.
2. **Simulated Annealing**: Shakes up patient assignments like a box of marbles and cools them down slowly to find a high-quality allocation incredibly fast.
3. **QAOA (Quantum)**: A cutting-edge physics simulation that acts like a simulated quantum computer to find the best configuration.

---

## 🚀 4. How to Use the App (Step-by-Step)

### Step 1: Choose a Scenario
In the sidebar, select **Mass Casualty (10 patients)** from the dropdown.

### Step 2: Choose a Solver
Select **Simulated Annealing** from the "Active optimization algorithm" dropdown. (It is fast, robust, and works wonderfully!).

### Step 3: Run it!
Click the red **🚀 Execute Optimization Run** button in the sidebar.

---

## 📊 5. How to Read your Results

Once the run is complete, the app splits the results into three easy-to-read tabs:

* **📊 Allocation Results**:
  * See a simple table showing exactly where each patient was sent and how far they have to travel.
  * Click **Download Assignment CSV** to save these results to your computer.
  * See a summary showing how full each hospital is.
* **📈 Visualization Dashboard**:
  * **Distance Heatmap**: Dark blue blocks show close trips; light blue blocks show far trips.
  * **Bar Chart**: Easily compare how many patients were sent to each hospital (dark blue) versus how many total beds they actually have (yellow).
* **🔬 Quantum Formulation**:
  * Shows the exact math equations and a blueprint diagram of the simulated quantum circuit used to calculate the solution!
