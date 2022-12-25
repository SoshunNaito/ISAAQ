from isaaq.Common.QubitMapping import *
from isaaq.Common.QubitMappingProblem import *
from isaaq.Solver.BaseQAPSolver import *
from isaaq.Problem.QAPGenerator import *

class BaseQAPScheduler:
	def __init__(self, solver: BaseQAPSolver):
		self.solver = solver

	def _solve_main(self, problems: list[QubitMappingProblem]) -> list[QubitMapping]:
		raise RuntimeError("スケジューラが実装されていません")

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

		# print("before")
		# for mappingResult in mappingResults[:-1]:
		# 	a = []
		# 	for q_p in mappingResult:
		# 		s = "." if q_p == -1 else str(q_p)
		# 		s += "".join([" "] * (3 - len(s)))
		# 		a.append(s)
		# 	print("".join(a))

		intervals: list[Tuple[int, int, int]] = []
		for q_v in range(N_v):
			prev = -1
			for layer_idx, mappingResult in enumerate(mappingResults):
				if(mappingResult[q_v] != -1):
					if(layer_idx - prev > 1): intervals.append((q_v, prev, layer_idx))
					prev = layer_idx
		intervals.sort(key = lambda x: x[2] - x[1])

		INF = 1000000000
		for q_v, idx0, idx1 in intervals:
			distances = [[INF for q_p in range(N_p)] for _ in range(idx1 - idx0 - 1)]
			backs = [[-1 for q_p in range(N_p)] for _ in range(idx1 - idx0 - 1)]

			for q_pr in range(N_p):
				if(emptySpaces[idx0 + 1][q_pr] == 0):
					continue
				if(idx0 == -1):
					distances[0][q_pr] = 0
				else:
					q_pl = mappingResults[idx0][q_v]
					distances[0][q_pr] = device.cost.cost_swap[q_pl][q_pr]
					backs[0][q_pr] = q_pl


			for idx in range(idx0 + 1, idx1 - 1):
				for q_pl in range(N_p):
					if(emptySpaces[idx][q_pl] == 0):
						continue
					d0 = distances[idx - idx0 - 1][q_pl]
					for q_pr in range(N_p):
						if(emptySpaces[idx + 1][q_pr] == 0):
							continue
						d = d0 + device.cost.cost_swap[q_pl][q_pr]
						if(d < distances[idx - idx0][q_pr]):
							distances[idx - idx0][q_pr] = d
							backs[idx - idx0][q_pr] = q_pl

			dist, back = INF, -1
			for q_pl in range(N_p):
				if(emptySpaces[idx1 - 1][q_pl] == 0):
					continue
				if(idx1 == len(mappingResults) - 1):
					d = distances[idx1 - idx0 - 2][q_pl]
				else:
					q_pr = mappingResults[idx1][q_v]
					d = distances[idx1 - idx0 - 2][q_pl] + device.cost.cost_swap[q_pl][q_pr]
				if(d < dist):
					dist = d
					back = q_pl

			# DP復元
			for idx in range(idx0 + 1, idx1)[::-1]:
				mappingResults[idx][q_v] = back
				emptySpaces[idx][back] -= 1
				back = backs[idx - idx0 - 1][back]

		# print("after")
		# for mappingResult in mappingResults[:-1]:
		# 	a = []
		# 	for q_p in mappingResult:
		# 		s = "." if q_p == -1 else str(q_p)
		# 		s += "".join([" "] * (3 - len(s)))
		# 		a.append(s)
		# 	print("".join(a))

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

		if(self.solver.reduce_unused_qubits):
			self._fill_qubits(answers)
		
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