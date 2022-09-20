from isaaq.Common.QubitMapping import *
from isaaq.Common.QubitMappingProblem import *
from isaaq.Solver.BaseQAPSolver import *
from isaaq.Problem.QAPGenerator import *

class BaseQAPScheduler:
	def __init__(self, solver: BaseQAPSolver):
		self.solver = solver

	def _solve_main(self, problems: list[QubitMappingProblem]) -> list[QubitMapping]:
		raise RuntimeError("ソルバーが実装されていません")

	def solve(self, problem: QubitMappingProblem, reset_solver: bool = True) -> QubitMapping:
		problems = GenerateQAPList(problem, self.solver.max_binary_variables)
		if(reset_solver): self.solver.reset()

		answers = self._solve_main(problems)
		if(len(answers) != len(problems)):
			raise RuntimeError("問題と解のサイズが異なります")
		
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