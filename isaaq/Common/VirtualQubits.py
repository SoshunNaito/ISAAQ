from isaaq.Common.Qubits import *

class VirtualQubits(Qubits):
	def __init__(self, N: int, sizes: list[int] = None):
		super().__init__(N, sizes)