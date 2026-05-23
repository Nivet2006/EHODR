import numpy as np
from itertools import product

def solve_exact(n_patients, hospitals, beds, vents, staff, severity, distance, specialties=False):
    n_hospitals = len(hospitals)
    best_cost = np.inf
    best_assign = None
    
    for assign in product(range(n_hospitals), repeat=n_patients):
        used_beds = [0]*n_hospitals
        used_vents = [0]*n_hospitals
        used_staff = [0]*n_hospitals
        feasible = True
        cost = 0
        
        for p, h_idx in enumerate(assign):
            used_beds[h_idx] += 1
            used_vents[h_idx] += 1
            used_staff[h_idx] += 1
            cost += severity[p] * distance[p][h_idx]
            
            if (used_beds[h_idx] > beds[hospitals[h_idx]] or
                used_vents[h_idx] > vents[hospitals[h_idx]] or
                used_staff[h_idx] > staff[hospitals[h_idx]]):
                feasible = False
                break
                
        if specialties and feasible:
            for p in range(n_patients):
                if severity[p] >= 3 and assign[p] != 0:
                    feasible = False
                    break
                    
        if feasible and cost < best_cost:
            best_cost = cost
            best_assign = assign
            
    return best_cost, best_assign

# 1. Mass Casualty
n_patients = 10
n_hospitals = 3
beds = {"H1": 8, "H2": 6, "H3": 4}
vents = {"H1": 6, "H2": 4, "H3": 3}
staff = {"H1": 5, "H2": 4, "H3": 2}
np.random.seed(42)
severity = np.random.randint(1, 4, n_patients)
distance = np.random.randint(1, 20, (n_patients, n_hospitals))
hospitals = [f"H{i+1}" for i in range(n_hospitals)]
cost_mc, assign_mc = solve_exact(n_patients, hospitals, beds, vents, staff, severity, distance)
print("=== Mass Casualty Preset ===")
print("Optimal Cost:", cost_mc)
print("Optimal Allocations:", [hospitals[idx] for idx in assign_mc])

# 2. Pandemic Surge
n_patients = 12
n_hospitals = 3
beds = {"H1": 10, "H2": 8, "H3": 6}
vents = {"H1": 8, "H2": 6, "H3": 4}
staff = {"H1": 7, "H2": 5, "H3": 3}
np.random.seed(42)
severity = np.random.randint(1, 4, n_patients)
distance = np.random.randint(1, 20, (n_patients, n_hospitals))
hospitals = [f"H{i+1}" for i in range(n_hospitals)]
cost_ps, assign_ps = solve_exact(n_patients, hospitals, beds, vents, staff, severity, distance)
print("\n=== Pandemic Surge Preset ===")
print("Optimal Cost:", cost_ps)
print("Optimal Allocations:", [hospitals[idx] for idx in assign_ps])

# 3. Earthquake
n_patients = 8
n_hospitals = 2
beds = {"H1": 6, "H2": 5}
vents = {"H1": 5, "H2": 4}
staff = {"H1": 4, "H2": 4}
np.random.seed(42)
severity = np.random.randint(1, 4, n_patients)
distance = np.random.randint(1, 20, (n_patients, n_hospitals))
hospitals = [f"H{i+1}" for i in range(n_hospitals)]
cost_eq, assign_eq = solve_exact(n_patients, hospitals, beds, vents, staff, severity, distance)
print("\n=== Earthquake Preset (No Specialties) ===")
print("Optimal Cost:", cost_eq)
print("Optimal Allocations:", [hospitals[idx] for idx in assign_eq])

cost_eq_spec, assign_eq_spec = solve_exact(n_patients, hospitals, beds, vents, staff, severity, distance, specialties=True)
print("\n=== Earthquake Preset (With Specialties) ===")
print("Optimal Cost:", cost_eq_spec)
print("Optimal Allocations:", [hospitals[idx] for idx in assign_eq_spec])
