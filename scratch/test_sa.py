import numpy as np
from simanneal import Annealer

n_patients = 10
n_hospitals = 3
beds = {"H1": 8, "H2": 6, "H3": 4}
vents = {"H1": 6, "H2": 4, "H3": 3}
staff = {"H1": 5, "H2": 4, "H3": 2}

np.random.seed(42)
severity = np.random.randint(1, 4, n_patients)
distance = np.random.randint(1, 20, (n_patients, n_hospitals))
hospitals = [f"H{i+1}" for i in range(n_hospitals)]

class HospitalAllocationAnnealer(Annealer):
    def __init__(self, state):
        super().__init__(state)
    
    def move(self):
        p = np.random.randint(0, n_patients)
        new_h = np.random.randint(0, len(hospitals))
        self.state[p] = new_h
    
    def energy(self):
        cost = 0
        used_beds = [0]*len(hospitals)
        used_vents = [0]*len(hospitals)
        used_staff = [0]*len(hospitals)
        
        for p, h_idx in enumerate(self.state):
            used_beds[h_idx] += 1
            used_vents[h_idx] += 1
            used_staff[h_idx] += 1
            cost += severity[p] * distance[p][h_idx]
            
        penalty_strength = 1000.0
        for h_idx, h in enumerate(hospitals):
            if used_beds[h_idx] > beds[h]:
                cost += penalty_strength * (used_beds[h_idx] - beds[h])
            if used_vents[h_idx] > vents[h]:
                cost += penalty_strength * (used_vents[h_idx] - vents[h])
            if used_staff[h_idx] > staff[h]:
                cost += penalty_strength * (used_staff[h_idx] - staff[h])
                
        return cost

# Let's run simulated annealing 10 times to check variability and optimal parameters
for i in range(10):
    init_state = np.random.randint(0, len(hospitals), n_patients)
    annealer = HospitalAllocationAnnealer(init_state)
    annealer.Tmax = 5000.0
    annealer.Tmin = 1.0
    annealer.steps = 5000  # Let's try 5000 steps
    state, energy = annealer.anneal()
    print(f"Run {i+1}: Energy = {energy}, State = {state}")
