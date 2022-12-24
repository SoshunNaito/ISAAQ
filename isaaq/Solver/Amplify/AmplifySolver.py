import os
import subprocess
from concurrent.futures import *

from isaaq.Common.QubitMapping import *
from isaaq.Common.QubitMappingProblem import *
from isaaq.Solver.BaseQAPSolver import *
from isaaq.IO.QubitMappingProblem import *
from isaaq.IO.QubitMappingResult import *
from isaaq.Solver.Amplify.AmplifySettings import *

from isaaq.Solver.Amplify.SubModule.AmplifyRunner import *
from isaaq.Solver.Amplify.SubModule.AmplifyIO import *

def CallAmplifyRunner(n: int, id: str) -> int:
	subRoutineFilePath = os.path.join(os.path.dirname(__file__), "SubModule/AmplifyRunner.py")
	subprocess.run(
		['python', subRoutineFilePath, id]
	)
	return n

class AmplifySolver(BaseQAPSolver):
	def __init__(self, settings: AmplifySettings):
		super().__init__()
		
		self.settings = settings
		self.reset()

	def reset(self):
		self.token = self.settings.token
		self.max_binary_variables = self.settings.max_binary_variables
		self.max_num_machines = self.settings.max_num_machines
		self.timeout = self.settings.timeout
		self.constraint_strength = self.settings.constraint_strength

	def solve(self, problem: QubitMappingProblem) -> QubitMapping:
		return self.solve_all([problem])[0]
	
	def solve_all(self, problems: list[QubitMappingProblem]) -> list[QubitMapping]:
		ids = [str(n) for n in range(len(problems))]
		for n in range(len(problems)):
			problem = problems[n]
			ExportProblem(
				problem,
				AmplifyRuntimeSettings(self.token, self.timeout, self.constraint_strength),
				ids[n]
			)
		with ThreadPoolExecutor(max_workers = self.max_num_machines) as pool:
			futures = [
				pool.submit(CallAmplifyRunner, n, ids[n])
				for n in range(len(problems))
			]
			for f in as_completed(futures):
				n = f.result()
				runtimeInfo = ImportResult(problems[n], ids[n])
				if(runtimeInfo.success == False):
					raise RuntimeError("failed at AmplifyRunner")
				
				if(self.constraint_strength < runtimeInfo.constraint_strength):
					self.constraint_strength = runtimeInfo.constraint_strength
					print("constraint_strength changed to " + str(self.constraint_strength))

		################## 確定していないqubitの割り当てを埋める ##################

		device = problems[0].physicalDevice
		N_v = problems[0].layers[0].virtualQubits.N
		N_p = device.qubits.N

		mappingResults: list[list[int]] = []
		candidates: list[list[list[int]]] = []
		emptySpaces: list[list[int]] = []
		for problem in problems:
			for layer in problem.layers:
				mappingResults.append(layer.virtualToPhysical)
				counts = [s for s in device.qubits.sizes]
				for q_p in layer.virtualToPhysical:
					if(q_p != -1): counts[q_p] -= 1
				emptySpaces.append(counts)
			for candidate in problem.candidates:
				candidates.append(candidate)
		mappingResults.append([-1 for _ in range(N_v)])


		for mappingResult in mappingResults[:-1]:
			s = "  ".join([("." if q_p == -1 else str(q_p)) for q_p in mappingResult])
			print(s)


		intervals: list[Tuple[int, int, int]] = []
		for q_v in range(N_v):
			prev = -1
			for layer_idx, mappingResult in enumerate(mappingResults):
				if(mappingResult[q_v] == -1):
					if(layer_idx - prev > 1): intervals.append((q_v, prev, layer_idx))
					prev = layer_idx
		intervals.sort(key = lambda x: x[2] - x[1])

		INF = 1000000000
		for q_v, idx0, idx1 in intervals:
			distances = [[INF for q_p in range(N_p)] for _ in range(idx1 - idx0 - 1)]
			backs = [[-1 for q_p in range(N_p)] for _ in range(idx1 - idx0 - 1)]

			if(idx0 != -1):
				q_pl = mappingResults[idx0][q_v]
				for q_pr in candidates[idx0 + 1][q_v]:
					if(emptySpaces[idx0 + 1][q_pr] == 0):
						continue
					distances[0][q_pr] = device.cost.cost_swap[q_pl][q_pr]
					backs[0][q_pr] = q_pl

			for idx in range(idx0 + 1, idx1 - 1):
				for q_pl in candidates[idx][q_v]:
					if(emptySpaces[idx][q_pl] == 0):
						continue
					d0 = distances[idx - idx0 - 1][q_pl]
					for q_pr in candidates[idx + 1][q_v]:
						if(emptySpaces[idx + 1][q_pr] == 0):
							continue
						d = d0 + device.cost.cost_swap[q_pl][q_pr]
						if(d < distances[idx - idx0][q_pr]):
							distances[idx - idx0][q_pr] = d
							backs[idx - idx0][q_pr] = q_pl

			dist, back = INF, -1
			for q_pl in candidates[idx1 - 1][q_v]:
				if(emptySpaces[idx1 - 1][q_pl] == 0):
					continue
				if(idx1 == len(candidates)):
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

		
		for mappingResult in mappingResults[:-1]:
			s = "  ".join([("." if q_p == -1 else str(q_p)) for q_p in mappingResult])
			print(s)


		answers = []
		for problem in problems:
			answer = QubitMapping(
				problem.physicalDevice,
				problem.layers
			)
			# self.evaluate(problem, answer)
			answers.append(answer)
		return answers