import sys

from isaaq.Common.QubitMappingProblem import *
from isaaq.Solver.Amplify.AmplifySettings import *
from isaaq.Solver.Amplify.SubModule.AmplifyIO import *
from isaaq.Solver.Amplify.SubModule.RuntimeDataTypes import *

from amplify import Solver, BinarySymbolGenerator
from amplify.client import FixstarsClient
from amplify.constraint import equal_to, clamp, one_hot

import time
from dataclasses import dataclass

@dataclass
class AmplifyExecutionInfo:
	num_trials: int = 0
	execution_time: float = 0
	cpu_time: float = 0
	queue_time: float = 0

# solve with Amplify
def solve_main(problem: QubitMappingProblem, settings: AmplifyRuntimeSettings, id: str) -> AmplifyExecutionInfo:
	info = AmplifyExecutionInfo()
	client = FixstarsClient()
	client.token = settings.token

	N_in = problem.layers[0].virtualQubits.N
	N_out = problem.physicalDevice.qubits.N
	M = problem.numLayers

	gen = BinarySymbolGenerator()
	# x = gen.array(M, N_in, N_out)
	x =	[
			[
				gen.array(len(problem.candidates[m][n_in])) for n_in in range(N_in)
			] for m in range(M)
		]

	constraint = 0
	for m in range(M):
		arr = [0 for n_out in range(N_out)]
		for n_in in range(N_in):
			# 行き先が必ず一つ存在する
			constraint += one_hot(x[m][n_in])
			# 行き先ごとにエッジを集計
			for idx_out in range(len(problem.candidates[m][n_in])):
				n_out = problem.candidates[m][n_in][idx_out]
				arr[n_out] += x[m][n_in][idx_out]
		for n_out in range(N_out):
			if(arr[n_out] == 0): continue

			# 行き先が集中して溢れることを防ぐ
			constraint += clamp(arr[n_out], 0, problem.physicalDevice.qubits.sizes[n_out])
			# constraint += equal_to(arr[n_out], problem.physicalDevice.qubits.sizes[n_out])

	deviceCost = problem.physicalDevice.cost

	cx_count = 0
	cost_cnot = 0
	for m in range(M):
		layer = problem.layers[m]
		for gate in layer.virtualGates:
			if(isinstance(gate, CXGate)):
				a, b = gate.Qubit_src, gate.Qubit_dst
				for i in range(len(problem.candidates[m][a])):
					p = problem.candidates[m][a][i]
					for j in range(len(problem.candidates[m][b])):
						q = problem.candidates[m][b][j]
						cost_cnot += x[m][a][i] * x[m][b][j] * deviceCost.cost_cnot[p][q]
				cx_count += 1

	cost_swap = 0
	for m in range(-1, M):
		if(m == -1):
			if(problem.left_layer != None and problem.left_strength > 0):
				for i in range(N_in):
					a = problem.left_layer.virtualToPhysical[i]
					for j in range(len(problem.candidates[0][i])):
						b = problem.candidates[0][i][j]
						cost_swap += x[0][i][j] * deviceCost.cost_swap[a][b] * problem.left_strength
		elif(m == M - 1):
			if(problem.right_layer != None and problem.right_strength > 0):
				for i in range(N_in):
					b = problem.right_layer.virtualToPhysical[i]
					for j in range(len(problem.candidates[M - 1][i])):
						a = problem.candidates[M - 1][i][j]
						cost_swap += x[M - 1][i][j] * deviceCost.cost_swap[a][b] * problem.right_strength
		else:
			for i in range(N_in):
				for j in range(len(problem.candidates[m][i])):
					a = problem.candidates[m][i][j]
					for k in range(len(problem.candidates[m + 1][i])):
						b = problem.candidates[m + 1][i][k]
						cost_swap += x[m][i][j] * x[m + 1][i][k] * deviceCost.cost_swap[a][b]

	cost = cost_cnot + cost_swap
	cost /= cx_count

	client.parameters.timeout = settings.timeout
	solver = Solver(client)

	max_strength = settings.constraint_strength * (2 ** 50)
	strength = settings.constraint_strength
	while(strength < max_strength):
		model = cost + constraint * strength
		result = solver.solve(model)

		info.num_trials += 1
		info.execution_time += solver.execution_time
		info.cpu_time += solver.client_result.timing.cpu_time
		info.queue_time += solver.client_result.timing.queue_time
		
		if(len(result) > 0):
			mappingResult = QubitMapping(problem.physicalDevice)
			for m in range(M):
				answer = [-1 for _ in range(N_in)]
				for i in range(N_in):
					x_values = x[m][i].decode(result[0].values)
					for j in range(len(problem.candidates[m][i])):
						if(x_values[j] > 0.5):
							answer[i] = problem.candidates[m][i][j]
				layer = QubitMappingLayer(problem.layers[m].virtualQubits, [], answer)
				mappingResult.AddLayer(layer)
				
			ExportResult(
				mappingResult,
				AmplifyRuntimeInfo(strength),
				id
			)
			return info
		strength *= 2

	raise RuntimeError("No satisfiable solution found.")

import sys
if __name__ == "__main__":
	solve_start_time = time.time()
	id = sys.argv[1]

	(problem, settings) = ImportProblem(id)
	info = solve_main(problem, settings, id)

	time_ms = int((time.time() - solve_start_time) * 1000)

	s = ""
	if(info.num_trials == 1):
		s += id + " : " + str(time_ms) + "ms"
	else:
		s += id + " : " + str(time_ms) + "ms"
		s += " (" + str(info.num_trials) + " trials)"
	s += " exe: " + str(int(info.execution_time + 0.5)) + "ms"
	s += ", cpu: " + str(int(info.cpu_time + 0.5)) + "ms"
	s += ", que: " + str(int(info.queue_time + 0.5)) + "ms"
	print(s)