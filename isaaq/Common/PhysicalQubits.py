from isaaq.Common.Qubits import *

class PhysicalQubits(Qubits):
	def __init__(self, N: int, sizes: list[int] = None):
		super().__init__(N, sizes)