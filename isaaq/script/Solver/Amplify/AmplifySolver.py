import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from Common.QubitMapping import *
from Common.QubitMappingProblem import *
from Solver.BaseQAPSolver import *
from IO.QubitMappingProblem import *
from IO.QubitMappingResult import *
from .AmplifySettings import *

import subprocess
from concurrent.futures import *
from .SubModule.AmplifyRunner import *
from .SubModule.AmplifyIO import *

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
				if(self.constraint_strength < runtimeInfo.constraint_strength):
					self.constraint_strength = runtimeInfo.constraint_strength
					print("constraint_strength changed to " + str(self.constraint_strength))

		answers = []
		for problem in problems:
			answer = QubitMapping(
				problem.physicalDevice,
				problem.layers
			)
			self.evaluate(problem, answer)
			answers.append(answer)
		return answers