from isaaq.src.Common.QubitMapping import *

class QubitMappingProblem(QubitMapping):
	def __init__(
		self,
		device: PhysicalDevice, layers: list[QubitMappingLayer] = [],
		candidates: list[list[list[int]]] = None,
		left_layer: QubitMappingLayer = None, right_layer: QubitMappingLayer = None,
		left_strength: float = 1, right_strength: float = 1
	):
		super().__init__(device)
		if(candidates == None):
			candidates = [
				[
					list(range(self.physicalDevice.qubits.N))
					for v in range(layer.virtualQubits.N)
				]
				for layer in layers
			]
		self.SetProblemLayers(layers, candidates)
		self.SetBoundaries(left_layer, right_layer, left_strength, right_strength)

	def SetProblemLayers(self, layers: list[QubitMappingLayer], candidates: list[list[list[int]]]):
		if(len(candidates) != len(layers)):
			raise RuntimeError("candidatesの長さが正しくありません")

		self.layers = []
		self.candidates: list[list[list[int]]] = []
		for l in range(len(layers)):
			layer, candidate = layers[l], candidates[l]
			self.AddProblemLayer(layer, candidate)

	def AddProblemLayer(self, layer: QubitMappingLayer, candidate: list[list[int]]):
		if(len(candidate) != layer.virtualQubits.N):
			raise RuntimeError("candidatesの要素(仮想Qubit数)が正しくありません")
		for n in range(len(candidate)):
			if(len(candidate[n]) < 1 or len(candidate[n]) > self.physicalDevice.qubits.N):
				raise RuntimeError("candidatesの要素(物理Qubit数)が正しくありません")

		self.AddLayer(layer)
		self.candidates.append(candidate)

	def SetBoundaries(
		self,
		left_layer: QubitMappingLayer = None, right_layer: QubitMappingLayer = None,
		left_strength: float = 1, right_strength: float = 1
	):
		self.left_layer: QubitMappingLayer = left_layer
		self.right_layer: QubitMappingLayer = right_layer
		self.left_strength: float = left_strength
		self.right_strength: float = right_strength

	def __str__(self):
		s = str(self.physicalDevice) + ", " + str(self.numLayers) + " layers\n"
		s += "boundary(left) = " + str(self.left_strength) + ", " + str(self.left_layer) + "\n"
		s += "boundary(right) = " + str(self.right_strength) + ", " + str(self.right_layer) + "\n"
		for l in range(self.numLayers):
			layer, candidate = self.layers[l], self.candidates[l]
			s += "\t" + str(layer) + "\n"
			s += "\tcandidates = " + " ".join([str(len(c)) for c in candidate]) + "\n"
		return s