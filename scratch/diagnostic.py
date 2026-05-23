import qiskit
print("Qiskit version:", qiskit.__version__)

try:
    from qiskit_algorithms import QAOA
    print("Imported QAOA from qiskit_algorithms")
except Exception as e:
    print("Failed to import QAOA:", e)

try:
    from qiskit.primitives import StatevectorSampler
    print("Imported StatevectorSampler from qiskit.primitives")
except Exception as e:
    print("Failed to import StatevectorSampler:", e)

try:
    from qiskit.primitives import Sampler
    print("Imported Sampler from qiskit.primitives")
except Exception as e:
    print("Failed to import Sampler:", e)
