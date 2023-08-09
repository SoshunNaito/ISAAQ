from isaaq.Common.QuantumCircuit import *
from isaaq.Common.QuantumGates import *
from isaaq.Common.PhysicalDevice import *
from isaaq.Common.QubitMapping import *
from isaaq.Common.QubitMappingProblem import *
from isaaq.Common.VirtualQubits import *
from isaaq.Common.QuantumGateStack import *

def RemoveDuplicateGates(N: int, gates: list[BaseGate]) -> list[BaseGate]:
	ans: list[BaseGate] = []
	stack: QuantumGateStack = QuantumGateStack(N)

	for gate in gates:
		if(isinstance(gate, U3Gate)):
			stack.AddSingleGate(
				U3Gate(
					gate.Qubit,
					gate.theta, gate.phi, gate.lam
				)
			)
		elif(isinstance(gate, CXGate)):
			src, dst = gate.Qubit_src, gate.Qubit_dst

			(popped_CX, popped_U3) = stack.PopGates(src, QubitStatus.CONTROL)
			for g in popped_CX: ans.append(g)
			for g in popped_U3: ans.append(g)

			(popped_CX, popped_U3) = stack.PopGates(dst, QubitStatus.TARGET)
			for g in popped_CX: ans.append(g)
			for g in popped_U3: ans.append(g)

			stack.AddCXGate(src, dst)
		elif(isinstance(gate, MeasureGate)):
			stack.AddSingleGate(
				MeasureGate(
					gate.Qubit,
					gate.Cbit
				)
			)
		elif(isinstance(gate, BarrierGate)):
			pass
		else:
			raise RuntimeError("Unknown gate detected: " + str(gate))

	(popped_CXList, popped_U3) = stack.PopAllGates()
	for popped_CX in popped_CXList:
		for g in popped_CX: ans.append(g)
	for g in popped_U3: ans.append(g)

	return ans

def SimplifyCircuit(circuit: QuantumCircuit) -> QuantumCircuit:
	gates_src: list[BaseGate] = [g for g in circuit.gates]
	factor: int = 10
	D = factor
	while(D < len(gates_src) * factor):
		gates_dst: list[BaseGate] = []
		for d in range(0, len(gates_src), D):
			gates = gates_src[d : min(d + D, len(gates_src))]
			l0 = len(gates)
			while(True):
				gates = RemoveDuplicateGates(circuit.numQubits, gates)
				if(len(gates) == l0): break
				l0 = len(gates)
			gates_dst += gates

		gates_src = gates_dst
		D *= factor

	ans: QuantumCircuit = QuantumCircuit(circuit.Qubits, circuit.Cbits)
	for gate in gates_src: ans.AddGate(gate)
	return ans

def GenerateMappingProblem(
	circuit: QuantumCircuit, device: PhysicalDevice,
	maxLayerSize: int = -1, minLayerCount: int = 1,
	simplifyCircuit: bool = False
) -> QubitMappingProblem:

	if(simplifyCircuit): circuit = SimplifyCircuit(circuit)
	
	Qubits = VirtualQubits(len(circuit.indexToQubit))
	layers = [QubitMappingLayer(Qubits)]
	CX_count = 0
	for gate in circuit.gates:
		if(isinstance(gate, CXGate)): CX_count += 1
	if(maxLayerSize == -1): maxLayerSize = CX_count
	
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