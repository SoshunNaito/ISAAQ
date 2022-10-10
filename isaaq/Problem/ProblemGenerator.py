from isaaq.Common.QuantumCircuit import *
from isaaq.Common.QuantumGates import *
from isaaq.Common.PhysicalDevice import *
from isaaq.Common.QubitMapping import *
from isaaq.Common.QubitMappingProblem import *
from isaaq.Common.VirtualQubits import *

def GenerateMappingProblem(
	circuit: QuantumCircuit, device: PhysicalDevice,
	minLayerCount: int = 10, maxLayerSize: int = 20
) -> QubitMappingProblem:

	Qubits = VirtualQubits(len(circuit.indexToQubit))
	layers = [QubitMappingLayer(Qubits)]
	CX_count = 0
	for gate in circuit.gates:
		if(isinstance(gate, CXGate)): CX_count += 1
	
	if(CX_count <= minLayerCount): layer_count = CX_count
	elif(CX_count <= minLayerCount * maxLayerSize): layer_count = minLayerCount
	else: layer_count = (CX_count + maxLayerSize - 1) // maxLayerSize

	CX_idx, layer_idx = 0, 1
	for gate in circuit.gates:
		if(isinstance(gate, CXGate)):
			if(CX_idx >= layer_idx * CX_count // layer_count):
				layer_idx += 1
				layers.append(QubitMappingLayer(Qubits))
			CX_idx += 1
		layers[-1].AddGate(gate)
	
	return QubitMappingProblem(device, layers)