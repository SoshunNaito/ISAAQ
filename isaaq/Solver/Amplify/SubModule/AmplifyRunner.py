import sys

from isaaq.Common.QubitMappingProblem import *
from isaaq.Solver.Amplify.AmplifySettings import *
from isaaq.Solver.Amplify.SubModule.AmplifyIO import *
from isaaq.Solver.Amplify.SubModule.RuntimeDataTypes import *

from amplify import Solver, BinarySymbolGenerator
from amplify import InequalityFormulation
from amplify.client import FixstarsClient
from amplify.constraint import equal_to, one_hot, less_equal

import time

# solve with Amplify
def solve(problem: QubitMappingProblem, settings: AmplifyRuntimeSettings, id: str) -> AmplifyRuntimeInfo:
	try:
		solve_start_time = time.time()

		info = AmplifyRuntimeInfo()
		client = FixstarsClient()
		client.token = settings.token

		#################################################

		M = problem.numLayers
		N_v = problem.layers[0].virtualQubits.N
		N_p = problem.physicalDevice.qubits.N

		# 使われているvirtual qubitを列挙
		usedVirtualQubits: list[list[int]] = []
		for m in range(M):
			used_qubits: set[int] = set()
			if(settings.reduce_unused_qubits == False):
				for q_v in range(N_v): used_qubits.add(q_v)

			layer = problem.layers[m]
			for gate in layer.virtualGates:
				if(isinstance(gate, CXGate)):
					a, b = gate.Qubit_src, gate.Qubit_dst
					used_qubits.add(a)
					used_qubits.add(b)
			usedVirtualQubits.append(sorted(list(used_qubits)))

		virtualQubitToIndex: list[list[int]] = []
		for m in range(M):
			qubitToIndex = [0] * N_v
			for q_v in usedVirtualQubits[m]: qubitToIndex[q_v] = 1
			for q_v in range(N_v):
				if(q_v == 0): qubitToIndex[q_v] -= 1
				else: qubitToIndex[q_v] += qubitToIndex[q_v - 1]
			virtualQubitToIndex.append(qubitToIndex)

		# バイナリ変数を用意する
		gen = BinarySymbolGenerator()
		x =	[
				[
					gen.array(len(problem.candidates[m][q_v])) for q_v in usedVirtualQubits[m]
				] for m in range(M)
			]
		
		# 制約を追加する
		constraint = 0
		for m in range(M):
			arr = [0 for _ in range(N_p)]
			cnt = [0 for _ in range(N_p)]
			for idx_v, q_v in enumerate(usedVirtualQubits[m]):
				# 行き先が必ず一つ存在する
				constraint += one_hot(x[m][idx_v])
				# 行き先ごとにエッジを集計
				for idx_p, q_p in enumerate(problem.candidates[m][q_v]):
					arr[q_p] += x[m][idx_v][idx_p]
					cnt[q_p] += 1

			activeQubits: set[int] = set()
			qubitToIndex: list[int] = [-1] * N_p
			used_qubits = len(usedVirtualQubits[m])
			total_qubits = 0
			for q_p in range(N_p):
				if(arr[q_p] == 0): continue
				qubitToIndex[q_p] = len(activeQubits)
				activeQubits.add(q_p)
				total_qubits += problem.physicalDevice.qubits.sizes[q_p]

			# equal_to制約
			dummy_count = total_qubits - used_qubits
			extra_variables_dummy = dummy_count * len(activeQubits)

			# less_equal制約
			extra_variables_constraint = 0
			for q_p in activeQubits:
				size = problem.physicalDevice.qubits.sizes[q_p]
				k = 1
				while(k <= size):
					size, k = size - k, k * 2
					extra_variables_constraint += 1
				if(size > 0):
					extra_variables_constraint += 1
			
			# equal_to制約
			if(extra_variables_dummy <= extra_variables_constraint):
				dummy_qubits = gen.array(dummy_count, len(activeQubits))
				for dummy_idx in range(dummy_count):
					constraint += one_hot(dummy_qubits[dummy_idx, :])

				for q_p in range(N_p):
					if(arr[q_p] == 0): continue
					idx_p = qubitToIndex[q_p]
					constraint += equal_to(
						arr[q_p] + sum(dummy_qubits[:, idx_p]),
						problem.physicalDevice.qubits.sizes[q_p]
					)
			# less_equal制約
			else:
				for q_p in range(N_p):
					if(cnt[q_p] <= problem.physicalDevice.qubits.sizes[q_p]): continue
					constraint += less_equal(
						arr[q_p],
						problem.physicalDevice.qubits.sizes[q_p]
					)

		deviceCost = problem.physicalDevice.cost

		# CNOTゲートのコスト
		cx_count = 0
		cost_cnot = 0
		for m in range(M):
			layer = problem.layers[m]
			qubitToIndex = virtualQubitToIndex[m]

			cx_pairs: dict[Tuple[int, int], int] = dict()
			for gate in layer.virtualGates:
				if(isinstance(gate, CXGate)):
					q_va, q_vb = gate.Qubit_src, gate.Qubit_dst
					if((q_va, q_vb) in cx_pairs): cx_pairs[(q_va, q_vb)] += 1
					else: cx_pairs[(q_va, q_vb)] = 1
					cx_count += 1

			for (q_va, q_vb), weight in cx_pairs.items():
				idx_va, idx_vb = qubitToIndex[q_va], qubitToIndex[q_vb]
				for idx_pa, q_pa in enumerate(problem.candidates[m][q_va]):
					for idx_pb, q_pb in enumerate(problem.candidates[m][q_vb]):
						cost_cnot += x[m][idx_va][idx_pa] * x[m][idx_vb][idx_pb] * deviceCost.cost_cnot[q_pa][q_pb] * weight

		# SWAPゲートのコスト
		cost_swap = 0
		prev_layers = [None] * N_v
		for m_r in range(-1, M + 1):
			if(m_r == -1):
				if(problem.left_layer != None and problem.left_strength > 0):
					for q_v, q_p in enumerate(problem.left_layer.virtualToPhysical):
						if(q_p != -1): prev_layers[q_v] = -1

			elif(m_r == M):
				if(problem.right_layer != None and problem.right_strength > 0):
					for q_v, q_pr in enumerate(problem.right_layer.virtualToPhysical):
						m_l = prev_layers[q_v]
						if(q_pr == -1 or m_l in [-1, None]): continue

						factor = 0.5 ** (m_r - m_l - 1)
						strength = problem.right_strength * factor

						idx_v = virtualQubitToIndex[m_l][q_v]
						for idx_pl, q_pl in enumerate(problem.candidates[m_l][q_v]):
							cost_swap += x[m_l][idx_v][idx_pl] * deviceCost.cost_swap[q_pl][q_pr] * strength
			
			else:
				for idx_vr, q_v in enumerate(usedVirtualQubits[m_r]):
					m_l = prev_layers[q_v]
					prev_layers[q_v] = m_r
					if(m_l == None): continue

					factor = 0.5 ** (m_r - m_l - 1)
					strength = (problem.left_strength if m_l == -1 else 1) * factor

					for idx_pr, q_pr in enumerate(problem.candidates[m_r][q_v]):
						if(m_l == -1):
							q_pl = problem.left_layer.virtualToPhysical[q_v]
							cost_swap += x[m_r][idx_vr][idx_pr] * deviceCost.cost_swap[q_pl][q_pr] * strength
						else:
							idx_vl = virtualQubitToIndex[m_l][q_v]
							for idx_pl, q_pl in enumerate(problem.candidates[m_l][q_v]):
								cost_swap += x[m_l][idx_vl][idx_pl] * x[m_r][idx_vr][idx_pr] * deviceCost.cost_swap[q_pl][q_pr] * strength

		cost = cost_cnot + cost_swap
		cost = cost / cx_count

		info.preparing_time = int((time.time() - solve_start_time) * 1000)

		#################################################



		client.parameters.timeout = settings.timeout
		solver = Solver(client)

		max_strength = settings.constraint_strength * (2 ** 50)
		strength = settings.constraint_strength
		while(strength < max_strength):
			model = cost + constraint * strength
			result = solver.solve(model)

			info.constraint_strength = strength
			info.num_trials += 1
			info.execution_time += int(solver.execution_time)
			info.cpu_time += int(solver.client_result.timing.cpu_time)
			info.queue_time += int(solver.client_result.timing.queue_time)
			
			if(len(result) > 0):
				mappingResult = QubitMapping(problem.physicalDevice)
				for m in range(M):
					answer = [-1 for _ in range(N_v)]
					for idx_v, q_v in enumerate(usedVirtualQubits[m]):
						x_values = x[m][idx_v].decode(result[0].values)
						for idx_p, q_p in enumerate(problem.candidates[m][q_v]):
							if(x_values[idx_p] > 0.5): answer[q_v] = q_p
					layer = QubitMappingLayer(problem.layers[m].virtualQubits, [], answer)
					mappingResult.AddLayer(layer)

				info.elapsed_time = int((time.time() - solve_start_time) * 1000)
					
				ExportResult(
					mappingResult,
					info,
					id
				)
				return info
			strength *= 2

		raise RuntimeError("No satisfiable solution found.")
	except Exception as e:
		print(e)
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("at " + str(fname) + ", line " + str(exc_tb.tb_lineno))
		raise e

import sys
if __name__ == "__main__":
	id = sys.argv[1]

	(problem, settings) = ImportProblem(id)

	try:
		info = solve(problem, settings, id)
	except Exception as e:
		info = AmplifyRuntimeInfo()
		info.success = False
		ExportResult(None, info, id)

	s = ""
	if(info.success):
		if(info.num_trials == 1):
			s += id + " : " + str(info.elapsed_time) + "ms"
		else:
			s += id + " : " + str(info.elapsed_time) + "ms"
			s += " (" + str(info.num_trials) + " trials)"
		s += " prepare: " + str(info.preparing_time) + "ms"
		s += ", exe: " + str(info.execution_time) + "ms"
		s += ", cpu: " + str(info.cpu_time) + "ms"
		s += ", que: " + str(info.queue_time) + "ms"
	else:
		s += id + " : failure"
	print(s)