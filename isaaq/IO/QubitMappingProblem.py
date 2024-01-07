from isaaq.Common.QubitMappingProblem import *
from isaaq.IO.QuantumCircuit import *
from isaaq.IO.PhysicalDevice import *

def ExportMappingProblem(problem: QubitMappingProblem, filepath: str):
	S = []

	S.append(problem.physicalDevice.graph.name + "\n")
	S.append(problem.physicalDevice.cost.name + "\n")
	S.append(str(problem.numLayers) + " layers\n")
	for l in range(problem.numLayers):
		layer = problem.layers[l]
		candidates = problem.candidates[l]

		# virtualQubits
		S.append(" ".join([str(s) for s in layer.virtualQubits.sizes]) + "\n")
		for candidate in candidates:
			S.append(" ".join([str(s) for s in candidate]) + "\n")
		# virtualGates
		S.append(str(len(layer.virtualGates)) + " gates\n")
		for gate in layer.virtualGates:
			S.append(gate.write() + "\n")

	# boundaries(left)
	if(abs(problem.left_strength) < 0.00000001 or problem.left_layer == None):
		S.append("None\n")
	else:
		S.append(str(problem.left_strength) + "\n")
		S.append(" ".join([str(s) for s in problem.left_layer.virtualQubits.sizes]) + "\n")
		S.append(" ".join([str(s) for s in problem.left_layer.virtualToPhysical]) + "\n")
	# boundaries(right)
	if(abs(problem.right_strength) < 0.00000001 or problem.right_layer == None):
		S.append("None\n")
	else:
		S.append(str(problem.right_strength) + "\n")
		S.append(" ".join([str(s) for s in problem.right_layer.virtualQubits.sizes]) + "\n")
		S.append(" ".join([str(s) for s in problem.right_layer.virtualToPhysical]) + "\n")

	with open(filepath, "w") as f:
		f.writelines(S)

def ImportMappingProblem(filepath: str) -> QubitMappingProblem:
	with open(filepath, "r") as f:
		S = f.readlines()
	
	deviceGraphName = S[0].strip()
	deviceCostName = S[1].strip()
	device = ImportDeviceManually(deviceGraphName, deviceCostName, False, None) # GenerateFuncは呼び出されないのでNoneで大丈夫

	numLayers = int(S[2].strip().split()[0])
	layers: list[QubitMappingLayer] = []
	candidates: list[list[list[int]]] = []

	line_idx = 3
	for l in range(numLayers):
		# virtualQubits
		A = [int(a) for a in S[line_idx].strip().split()]
		line_idx += 1
		Qubits = VirtualQubits(len(A), A)
		
		candidate = []
		for i in range(len(A)):
			candidate.append([int(a) for a in S[line_idx].strip().split()])
			line_idx += 1
		candidates.append(candidate)

		# virtualGates
		numGates = int(S[line_idx].strip().split()[0])
		line_idx += 1
		gates: list[BaseGate] = []
		for n in range(numGates):
			s = S[line_idx].strip()
			line_idx += 1
			gates.append(ReadGate(s))

		layer = QubitMappingLayer(Qubits, gates)
		layers.append(layer)

	# boundaries(left)
	s = S[line_idx].strip()
	line_idx += 1
	if(s[:4] == "None"):
		left_strength, left_layer = 0, None
	else:
		left_strength = float(s)
		A = [int(a) for a in S[line_idx].strip().split()]
		line_idx += 1
		left_Qubits = VirtualQubits(len(A), A)
		left_virtualToPhysical = [int(a) for a in S[line_idx].strip().split()]
		line_idx += 1
		left_layer = QubitMappingLayer(left_Qubits, [], left_virtualToPhysical)

	# boundaries(right)
	s = S[line_idx].strip()
	line_idx += 1
	if(s[:4] == "None"):
		right_strength, right_layer = 0, None
	else:
		right_strength = float(s)
		A = [int(a) for a in S[line_idx].strip().split()]
		line_idx += 1
		right_Qubits = VirtualQubits(len(A), A)
		right_virtualToPhysical = [int(a) for a in S[line_idx].strip().split()]
		line_idx += 1
		right_layer = QubitMappingLayer(right_Qubits, [], right_virtualToPhysical)
	
	return QubitMappingProblem(
		device, layers, candidates,
		left_layer, right_layer, left_strength, right_strength
	)