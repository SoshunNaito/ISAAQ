class Qubits:
	def __init__(self, N: int, sizes: list[int] = None):
		self.N = N
		self.numQubits = N
		self.sizes = [1 for _ in range(N)]
		if(sizes != None):
			self.setSizes(sizes)

	def setSizes(self, sizes: list[int]):
		if(len(sizes) != self.N):
			raise RuntimeError("sizesの長さが異なります")
		self.N = len(sizes)
		self.numQubits = sum(sizes)
		self.sizes = [s for s in sizes]

class VirtualQubits(Qubits):
	def __init__(self, N: int, sizes: list[int] = None):
		super().__init__(N, sizes)

class PhysicalQubits(Qubits):
	def __init__(self, N: int, sizes: list[int] = None):
		super().__init__(N, sizes)