from isaaq.Common.QuantumCircuit import *
from isaaq.Common.QuantumGates import *
from isaaq.Common.PhysicalDevice import *
from isaaq.Common.QubitMapping import *
from isaaq.Common.QubitMappingProblem import *
from isaaq.Common.VirtualQubits import *

MIN_LAYER_COUNT = 10 # レイヤーの最小枚数
MAX_LAYER_SIZE = 20 # 1レイヤーに含まれるCXの個数

def _CalcLayerCount(CX_count: int) -> int:
	if(CX_count <= MIN_LAYER_COUNT): return CX_count
	elif(CX_count <= MIN_LAYER_COUNT * MAX_LAYER_SIZE): return MIN_LAYER_COUNT
	else: return (CX_count + MAX_LAYER_SIZE - 1) // MAX_LAYER_SIZE

def GenerateMappingProblem(circuit: QuantumCircuit, device: PhysicalDevice) -> QubitMappingProblem:
	Qubits = VirtualQubits(len(circuit.indexToQubit))
	layers = [QubitMappingLayer(Qubits)]
	CX_count = 0
	for gate in circuit.gates:
		if(isinstance(gate, CXGate)): CX_count += 1
	layer_count = _CalcLayerCount(CX_count)

	CX_idx, layer_idx = 0, 1
	for gate in circuit.gates:
		if(isinstance(gate, CXGate)):
			if(CX_idx >= layer_idx * CX_count // layer_count):
				layer_idx += 1
				layers.append(QubitMappingLayer(Qubits))
			CX_idx += 1
		layers[-1].AddGate(gate)
	
	return QubitMappingProblem(device, layers)