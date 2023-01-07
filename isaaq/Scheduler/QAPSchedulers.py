from isaaq.Common.QubitMapping import *
from isaaq.Common.QubitMappingProblem import *
from isaaq.Solver.BaseQAPSolver import *
from isaaq.Problem.QAPGenerator import *

import numpy as np
from ortools.graph.python import min_cost_flow

class BaseQAPScheduler:
	def __init__(self, solver: BaseQAPSolver):
		self.solver = solver

	def _solve_main(self, problems: list[QubitMappingProblem]) -> list[QubitMapping]:
		raise RuntimeError("スケジューラが実装されていません")

	def _fill_intervals_dijkstra(
		self,
		N_v: int, N_p: int, swap_cost: list[list[float]],
		mappingResults: list[list[int]],
		emptySpaces: list[list[int]],
		intervals: list[Tuple[int, int, int]]
	):
		INF = 1000000000
		for q_v, idx0, idx1 in intervals:
			distances = [[INF for q_p in range(N_p)] for _ in range(idx1 - idx0)]
			backs = [[-1 for q_p in range(N_p)] for _ in range(idx1 - idx0)]

			for q_pr in range(N_p):
				if(emptySpaces[idx0][q_pr] == 0):
					continue
				if(idx0 == 0):
					distances[0][q_pr] = 0
				else:
					q_pl = mappingResults[idx0 - 1][q_v]
					distances[0][q_pr] = swap_cost[q_pl][q_pr]
					backs[0][q_pr] = q_pl

			for idx in range(idx0, idx1 - 1):
				for q_pl in range(N_p):
					if(emptySpaces[idx][q_pl] == 0):
						continue
					d0 = distances[idx - idx0][q_pl]
					for q_pr in range(N_p):
						if(emptySpaces[idx + 1][q_pr] == 0):
							continue
						d = d0 + swap_cost[q_pl][q_pr]
						if(d < distances[idx - idx0 + 1][q_pr]):
							distances[idx - idx0 + 1][q_pr] = d
							backs[idx - idx0 + 1][q_pr] = q_pl

			dist, back = INF, -1
			for q_pl in range(N_p):
				if(emptySpaces[idx1 - 1][q_pl] == 0):
					continue
				if(idx1 == len(mappingResults) - 1):
					d = distances[idx1 - idx0 - 1][q_pl]
				else:
					q_pr = mappingResults[idx1][q_v]
					d = distances[idx1 - idx0 - 1][q_pl] + swap_cost[q_pl][q_pr]
				if(d < dist):
					dist = d
					back = q_pl

			# DP復元
			for idx in range(idx0, idx1)[::-1]:
				mappingResults[idx][q_v] = back
				emptySpaces[idx][back] -= 1
				back = backs[idx - idx0][back]

	def _fill_intervals(
		self,
		N_v: int, N_p: int, swap_cost: list[list[float]],
		mappingResults: list[list[int]],
		emptySpaces: list[list[int]]
	):
		N_l = len(mappingResults) - 1

		intervals: list[Tuple[int, int, int]] = []
		lower_block: list[int] = [0] * N_v
		upper_block: list[int] = [0] * N_v
		for q_v in range(N_v):
			prev = 0
			for layer_idx, mappingResult in enumerate(mappingResults):
				if(mappingResult[q_v] != -1):
					if(prev == 0): lower_block[q_v] = layer_idx
					elif(layer_idx == N_l): upper_block[q_v] = prev
					elif(layer_idx - prev > 0): intervals.append((q_v, prev, layer_idx))
					prev = layer_idx + 1

		self._fill_intervals_dijkstra(
			N_v, N_p, swap_cost,
			mappingResults, emptySpaces,
			sorted(intervals, key = lambda x: x[1] - x[2])
		)

		lower_source = 0
		lower_sinks = list(range(1, N_v + 1))
		upper_sources = list(range(N_v + 1, N_v * 2 + 1))
		upper_sink = N_v * 2 + 1
		offset = N_v * 2 + 2

		islands_in = [
			[
				(q_p + l_idx * N_p) * 2 + offset
				for q_p in range(N_p)
			]
			for l_idx in range(N_l)
		]
		islands_out = [
			[
				(q_p + l_idx * N_p) * 2 + offset + 1
				for q_p in range(N_p)
			]
			for l_idx in range(N_l)
		]

		lower_flow, upper_flow = 0, 0
		for v_idx in range(N_v):
			if(lower_block[v_idx] != 0): lower_flow += 1
			if(upper_block[v_idx] != N_l): upper_flow += 1

		# start, end, caps, costs
		edges: list[Tuple[int, int, int, float]] = []

		# lower_source -> islands
		for p_idx in range(N_p):
			u = lower_source
			v = islands_in[0][p_idx]
			edges.append((u, v, N_v, 0))

		# islands -> lower_sinks
		for v_idx in range(N_v):
			if(lower_block[v_idx] == 0): continue
			l_idx = lower_block[v_idx]
			p = mappingResults[l_idx][v_idx]

			for p_idx in range(N_p):
				u = islands_out[l_idx - 1][p_idx]
				v = lower_sinks[v_idx]
				edges.append((u, v, 1, swap_cost[p_idx][p]))

		# upper_sources -> islands
		for v_idx in range(N_v):
			if(upper_block[v_idx] == N_l): continue
			l_idx = upper_block[v_idx]
			p = mappingResults[l_idx - 1][v_idx]

			for p_idx in range(N_p):
				u = upper_sources[v_idx]
				v = islands_in[l_idx][p_idx]
				edges.append((u, v, 1, swap_cost[p][p_idx]))

		# islands -> upper_sink
		for p_idx in range(N_p):
			u = islands_out[N_l - 1][p_idx]
			v = upper_sink
			edges.append((u, v, N_v, 0))

		# islands -> islands
		for l_idx in range(N_l):
			# set caps
			for p_idx in range(N_p):
				u = islands_in[l_idx][p_idx]
				v = islands_out[l_idx][p_idx]
				edges.append((u, v, emptySpaces[l_idx][p_idx], 0))
			# set costs
			if(l_idx == 0): continue
			for p_idx_0 in range(N_p):
				for p_idx_1 in range(N_p):
					u = islands_out[l_idx - 1][p_idx_0]
					v = islands_in[l_idx][p_idx_1]
					edges.append((u, v, N_v, swap_cost[p_idx_0][p_idx_1]))

		# prepare edges
		start, end, caps, costs = [], [], [], []
		for u, v, c, cs in edges:
			start.append(u)
			end.append(v)
			caps.append(c)
			costs.append(cs * 100)

		supplies_lower, supplies_upper = [lower_flow], [0]
		for v_idx in range(N_v):
			if(lower_block[v_idx] == 0):
				supplies_lower.append(0)
				supplies_upper.append(0)
			else:
				supplies_lower.append(-1)
				supplies_upper.append(0)
		for v_idx in range(N_v):
			if(upper_block[v_idx] == N_l):
				supplies_lower.append(0)
				supplies_upper.append(0)
			else:
				supplies_lower.append(0)
				supplies_upper.append(1)
		supplies_lower.append(0)
		supplies_upper.append(-upper_flow)
		
		for supplies in [supplies_lower, supplies_upper]:

			smcf = min_cost_flow.SimpleMinCostFlow()
			smcf.add_arcs_with_capacity_and_unit_cost(
				np.array(start),
				np.array(end),
				np.array(caps),
				np.array(costs)
			)
			for count, supply in enumerate(supplies):
				smcf.set_node_supply(count, supply)

			# solve
			status = smcf.solve()
			if status != smcf.OPTIMAL:
				print('There was an issue with the min cost flow input.')
				print(f'Status: {status}')
				exit(1)

			# decode
			placements_lower: list[list[list[int]]] = [
				[
					[] for p_idx in range(N_p)
				]
				for l_idx in range(N_l)
			]
			placements_upper: list[list[list[int]]] = [
				[
					[] for p_idx in range(N_p)
				]
				for l_idx in range(N_l)
			]
			paths: list[list[list[int]]] = [
				[
					[
						0 for p_idx_1 in range(N_p)
					]
					for p_idx_0 in range(N_p)
				]
				for l_idx in range(N_l - 1)
			]

			for i in range(smcf.num_arcs()):
				u, v, f, c = smcf.tail(i), smcf.head(i), smcf.flow(i), smcf.unit_cost(i)
				if(u == lower_source or v == upper_sink): continue
				if(f == 0): continue

				if(v >= lower_sinks[0] and v < lower_sinks[0] + N_v):
					v_idx = v - lower_sinks[0]
					l_idx = lower_block[v_idx] - 1
					p_idx = (u - islands_out[l_idx][0]) // 2

					mappingResults[l_idx][v_idx] = p_idx
					emptySpaces[l_idx][p_idx] -= 1
					placements_lower[l_idx][p_idx].append(v_idx)
				
				elif(u >= upper_sources[0] and u < upper_sources[0] + N_v):
					v_idx = u - upper_sources[0]
					l_idx = upper_block[v_idx]
					p_idx = (v - islands_in[l_idx][0]) // 2

					mappingResults[l_idx][v_idx] = p_idx
					emptySpaces[l_idx][p_idx] -= 1
					placements_upper[l_idx][p_idx].append(v_idx)

				elif(c != 0):
					n = (u - islands_out[0][0]) // 2
					l_idx, p_idx_0 = n // N_p, n % N_p

					n = (v - islands_in[0][0]) // 2
					p_idx_1 = n % N_p

					paths[l_idx][p_idx_0][p_idx_1] += f

			# fill in mappingResults
			for l_idx in range(1, N_l)[::-1]:
				for p_idx_1 in range(N_p):
					p_idx_0 = 0
					for v_idx in placements_lower[l_idx][p_idx_1]:
						while(paths[l_idx - 1][p_idx_0][p_idx_1] == 0):
							p_idx_0 += 1
						
						paths[l_idx - 1][p_idx_0][p_idx_1] -= 1
						mappingResults[l_idx - 1][v_idx] = p_idx_0
						emptySpaces[l_idx - 1][p_idx_0] -= 1
						placements_lower[l_idx - 1][p_idx_0].append(v_idx)
			
			for l_idx in range(N_l - 1):
				for p_idx_0 in range(N_p):
					p_idx_1 = 0
					for v_idx in placements_upper[l_idx][p_idx_0]:
						while(paths[l_idx][p_idx_0][p_idx_1] == 0):
							p_idx_1 += 1
						
						paths[l_idx][p_idx_0][p_idx_1] -= 1
						mappingResults[l_idx + 1][v_idx] = p_idx_1
						emptySpaces[l_idx + 1][p_idx_1] -= 1
						placements_upper[l_idx + 1][p_idx_1].append(v_idx)


	def _fill_qubits(self, answers: list[QubitMapping]):
		################# 確定していないqubitの割り当てを埋める ##################

		device = answers[0].physicalDevice
		N_v = answers[0].layers[0].virtualQubits.N
		N_p = device.qubits.N

		mappingResults: list[list[int]] = []
		emptySpaces: list[list[int]] = []
		for answer in answers:
			for layer in answer.layers:
				mappingResults.append([q_p for q_p in layer.virtualToPhysical])
				counts = [s for s in device.qubits.sizes]
				for q_p in layer.virtualToPhysical:
					if(q_p != -1): counts[q_p] -= 1
				emptySpaces.append(counts)
		mappingResults.append([0 for _ in range(N_v)])

		self._fill_intervals(N_v, N_p, device.cost.cost_swap, mappingResults, emptySpaces)

		total_cost = 0
		for q_v in range(N_v):
			for layer_idx in range(len(mappingResults) - 1):
				q_pl = mappingResults[layer_idx][q_v]
				q_pr = mappingResults[layer_idx + 1][q_v]
				total_cost += device.cost.cost_swap[q_pl][q_pr]
		print("total_cost = " + str(total_cost))

		idx = 0
		for answer in answers:
			for layer in answer.layers:
				for q_v, q_p in enumerate(mappingResults[idx]):
					layer.virtualToPhysical[q_v] = q_p
				idx += 1

	def solve(self, problem: QubitMappingProblem, reset_solver: bool = True) -> QubitMapping:
		problems = GenerateQAPList(
			problem,
			self.solver.max_binary_variables,
			self.solver.reduce_unused_qubits
		)
		if(reset_solver): self.solver.reset()

		answers = self._solve_main(problems)
		if(len(answers) != len(problems)):
			raise RuntimeError("問題と解のサイズが異なります")

		print("before")
		for answer in answers:
			for layer in answer.layers:
				used_gates: set[int] = set()
				for gate in layer.virtualGates:
					if(isinstance(gate, CXGate)):
						used_gates.add(gate.Qubit_src)
						used_gates.add(gate.Qubit_dst)
				a = []
				for q_v in range(len(layer.virtualToPhysical)):
					if(q_v not in used_gates): layer.virtualToPhysical[q_v] = -1
					q_p = layer.virtualToPhysical[q_v]
					s = ("." if q_p == -1 else chr(ord("A") + q_p % 60))
					a.append(s)
				print("".join(a))

		self._fill_qubits(answers)

		print("after")
		for answer in answers:
			for layer in answer.layers:
				a = []
				for q_p in layer.virtualToPhysical:
					s = ("." if q_p == -1 else chr(ord("A") + q_p % 60))
					a.append(s)
				print("".join(a))
		
		answer = QubitMapping(problem.physicalDevice)
		for a in answers:
			for layer in a.layers:
				answer.AddLayer(layer)
		return answer

class IndependentQAPScheduler(BaseQAPScheduler):
	def _solve_main(self, problems: list[QubitMappingProblem]) -> list[QubitMapping]:
		return self.solver.solve_all(problems)

class SequentialQAPScheduler(BaseQAPScheduler):
	def _solve_main(self, problems: list[QubitMappingProblem]) -> list[QubitMapping]:
		answers: list[QubitMapping] = []
		for i in range(len(problems)):
			problem = problems[i]
			if(i > 0):
				problem.SetBoundaries(
					left_layer = answers[i-1].layers[-1], right_layer = None,
					left_strength = 1.0, right_strength = 0
				)
			answers.append(self.solver.solve(problem))
		return answers

class BinaryQAPScheduler(BaseQAPScheduler):
	def _solve_main(self, problems: list[QubitMappingProblem]) -> list[QubitMapping]:
		num_problems = len(problems)
		answers: list[QubitMapping] = [None] * num_problems
		left: list[int] = [0] * num_problems
		right: list[int] = [0] * num_problems

		k = 1
		levels: list[list[int]] = []
		while(k < num_problems + 1):
			level: list[int] = []
			for _i in range(k, num_problems + 1, k * 2):
				i = _i - 1
				level.append(i)
				left[i], right[i] = i - k, i + k
			levels.append(level)
			k *= 2
		
		for level_idx in range(len(levels))[::-1]:
			level = levels[level_idx]
			prob_list: list[QubitMappingProblem] = []
			for i in level:
				problem = problems[i]
				l, r = left[i], right[i]
				if(l >= 0): problem.SetBoundaries(left_layer = answers[l].layers[-1], left_strength = 2 ** (-level_idx))
				if(r < num_problems): problem.SetBoundaries(right_layer = answers[r].layers[0], right_strength = 2 ** (-level_idx))
				prob_list.append(problem)

			results = self.solver.solve_all(prob_list)
			for i in range(len(level)):
				answers[level[i]] = results[i]
		return answers

class OddEvenQAPScheduler(BaseQAPScheduler):
	def _solve_main(self, problems: list[QubitMappingProblem]) -> list[QubitMapping]:
		num_problems = len(problems)
		answers: list[QubitMapping] = [None] * num_problems
		problems_odd = [problems[i] for i in range(1, len(problems), 2)]
		results_odd = self.solver.solve_all(problems_odd)

		for _i in range(len(results_odd)):
			i = _i * 2 + 1
			answers[i] = results_odd[_i]

		problems_even = []
		for i in range(0, len(problems), 2):
			problem = problems[i]
			l, r = i-1, i+1
			if(l >= 0): problem.SetBoundaries(left_layer = answers[l].layers[-1], left_strength = 1)
			if(r < num_problems): problem.SetBoundaries(right_layer = answers[r].layers[0], right_strength = 1)
			problems_even.append(problem)
		results_even = self.solver.solve_all(problems_even)

		for _i in range(len(results_even)):
			i = _i * 2
			answers[i] = results_even[_i]
		return answers