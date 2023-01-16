from isaaq.Common.QubitMapping import *
from isaaq.Common.QubitMappingProblem import *

class BaseQAPSolver:
	def __init__(self):
		self.max_binary_variables: int = -1
		self.reduce_unused_qubits: bool = False

	def evaluate(self, problem: QubitMappingProblem, answer: QubitMapping) -> bool:
		if(len(problem.candidates) != answer.numLayers):
			raise RuntimeError("解のレイヤー数が異なります")
		for l in range(answer.numLayers):
			if(len(problem.candidates[l]) != answer.layers[l].virtualQubits.N):
				raise RuntimeError("解の要素(仮想Qubit数)が正しくありません")
			for n in range(answer.layers[l].virtualQubits.N):
				if(answer.layers[l].virtualToPhysical[n] not in problem.candidates[l][n]):
					raise RuntimeError("解の要素(仮想Qubitの行き先)が正しくありません")
		return True

	def reset(self):
		pass

	def solve(self, problem: QubitMappingProblem) -> QubitMapping:
		raise RuntimeError("ソルバーが実装されていません")
	
	def solve_all(self, problems: list[QubitMappingProblem]) -> list[QubitMapping]:
		answers = []
		for problem in problems: answers.append(self.solve(problem))
		return answers