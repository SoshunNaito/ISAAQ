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
		activeIslands: set[int] = set()

		num_variables = 0
		for q_v, cands in enumerate(cands_list):
			if(q_v in usedQubitsList[layer_idx]):
				num_variables += len(cands)
				for q_p in cands: activeIslands.add(q_p)
		
		# less_equal制約
		extra_variables_constraint = 0
		for q_p in activeIslands:
			size = problem.physicalDevice.qubits.sizes[q_p]
			k = 1
			while(k <= size):
				size, k = size - k, k * 2
				extra_variables_constraint += 1
			if(size > 0):
				extra_variables_constraint += 1

		# equal_to制約
		extra_variables_dummy = 0
		for q_p in activeIslands:
			size = problem.physicalDevice.qubits.sizes[q_p]
			extra_variables_dummy += size
		extra_variables_dummy -= len(usedQubitsList[layer_idx])
		extra_variables_dummy *= len(activeIslands)

		extra_variables = min(extra_variables_constraint, extra_variables_dummy)
		num_variables += extra_variables
				
		sizes.append(num_variables)
		size_sum += num_variables
		size_max = max(size_max, num_variables)
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