import numpy as np
from itertools import product

n_patients = 10
n_hospitals = 3
beds = {"H1": 8, "H2": 6, "H3": 4}
vents = {"H1": 6, "H2": 4, "H3": 3}
staff = {"H1": 5, "H2": 4, "H3": 2}

np.random.seed(42)
severity = np.random.randint(1, 4, n_patients)
distance = np.random.randint(1, 20, (n_patients, n_hospitals))
hospitals = [f"H{i+1}" for i in range(n_hospitals)]

print("Severity:", severity.tolist())
print("Distance:\n", distance.tolist())

# Exact Solver
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
            
    if feasible and cost < best_cost:
        best_cost = cost
        best_assign = assign

print("Best Cost:", best_cost)
print("Best Assign:", best_assign)
if best_assign:
    for p, h_idx in enumerate(best_assign):
        print(f"Patient-{p+1}: H{h_idx+1} (dist: {distance[p][h_idx]}, severity: {severity[p]})")
