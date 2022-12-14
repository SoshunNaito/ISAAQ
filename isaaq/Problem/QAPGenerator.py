from isaaq.Common.QubitMapping import *
from isaaq.Common.QubitMappingProblem import *

def GenerateQAPList(problem: QubitMappingProblem, max_binary_variables: int = -1) -> list[QubitMappingProblem]:
	sizes = []
	size_sum, size_max = 0, 0
	for cands_list in problem.candidates:
		s = 0
		for cands in cands_list: s += len(cands)
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