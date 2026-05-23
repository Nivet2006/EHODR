from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import StatevectorSampler as Sampler
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_optimization.problems import QuadraticProgram

# Build a small dummy quadratic program
qp = QuadraticProgram()
qp.binary_var('x')
qp.binary_var('y')
qp.minimize(linear=[-1, -2], quadratic={('x', 'y'): 1})

# Initialize QAOA
sampler = Sampler()
qaoa = MinimumEigenOptimizer(QAOA(sampler=sampler, optimizer=COBYLA(), reps=1))
result = qaoa.solve(qp)
print("QAOA run successful!")
print("Result fval:", result.fval)
print("Result x:", result.x)
