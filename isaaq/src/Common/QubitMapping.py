from isaaq.src.Common.Qubits import *
from isaaq.src.Common.QuantumGates import *
from isaaq.src.Common.PhysicalDevice import *

class QubitMappingLayer:
	def __init__(
		self,
		Qubits: VirtualQubits = None,
		gates: list[BaseGate] = [],
		virtualToPhysical: list[int] = None
	):
		self.SetQubits(Qubits)
		self.SetGates(gates)
		self.SetMapping(virtualToPhysical)

	def SetQubits(self, Qubits: VirtualQubits):
		self.virtualQubits = Qubits

	def SetGates(self, gates: list[BaseGate]):
		self.virtualGates = [g for g in gates]

	def AddGate(self, gate: BaseGate):
		self.virtualGates.append(gate)
	
	def SetMapping(self, virtualToPhysical: list[int]):
		self.virtualToPhysical: list[int] = virtualToPhysical

	def __str__(self) -> str:
		CX_count, other_count = 0, 0
		for gate in self.virtualGates:
			if(isinstance(gate, CXGate)): CX_count += 1
			else: other_count += 1
		return str(self.virtualQubits.N) + "Qubits, " + str(CX_count) + " CNOTs + " + str(other_count) + " others, mapping: " + str(self.virtualToPhysical)

class QubitMapping:
	def __init__(self, device: PhysicalDevice, layers: list[QubitMappingLayer] = []):
		self.layers: list[QubitMappingLayer] = []
		self.numLayers = 0
		self.physicalDevice = device
		for layer in layers: self.AddLayer(layer)

	def AddLayer(self, layer: QubitMappingLayer):
		self.layers.append(layer)
		self.numLayers = len(self.layers)

	def __str__(self):
		s = str(self.physicalDevice) + ", " + str(self.numLayers) + " layers\n"
		for layer in self.layers: s += "\t" + str(layer) + "\n"
		return s