from isaaq.Common.QubitMapping import *
from isaaq.Common.QubitMappingProblem import *

def GenerateQAPList(
	problem: QubitMappingProblem,
	max_binary_variables: int = -1,
	reduce_unused_qubits: bool = False
) -> list[QubitMappingProblem]:

	usedQubitsList: list[set[int]] = []
	for layer in problem.layers:
		usedQubits: set[int] = set()
		if(reduce_unused_qubits == False):
			for q_v in range(layer.virtualQubits.N):
				usedQubits.add(q_v)
		else:
			for gate in layer.virtualGates:
				if(isinstance(gate, CXGate)):
					a, b = gate.Qubit_src, gate.Qubit_dst
					usedQubits.add(a)
					usedQubits.add(b)
		usedQubitsList.append(usedQubits)

	sizes = []
	size_sum, size_max = 0, 0
	for layer_idx, cands_list in enumerate(problem.candidates):
		s = 0
		for q_v, cands in enumerate(cands_list):
			if(q_v in usedQubitsList[layer_idx]):
				s += len(cands)
		sizes.append(s)
		size_sum += s
		size_max = max(size_max, s)
	if(max_binary_variables == -1):
		max_binary_variables = size_sum

	if(max_binary_variables < size_max): max_binary_variables = size_max

	ans = [QubitMappingProblem(problem.physicalDevice)]
	size_sum = 0
	for l in range(problem.numLayers):
		if(size_sum + sizes[l] > max_binary_variables):
			ans.append(QubitMappingProblem(problem.physicalDevice))
			size_sum = 0

		size_sum += sizes[l]
		ans[-1].AddProblemLayer(problem.layers[l], problem.candidates[l])

	return ans