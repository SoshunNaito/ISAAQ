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
		self.constraint_strength = self.settings.constraint_strength
		self.reduce_unused_qubits = self.settings.reduce_unused_qubits
		
		self.token = self.settings.token
		self.max_binary_variables = self.settings.max_binary_variables
		self.max_num_machines = self.settings.max_num_machines
		self.timeout = self.settings.timeout

	def solve(self, problem: QubitMappingProblem) -> QubitMapping:
		return self.solve_all([problem])[0]
	
	def solve_all(self, problems: list[QubitMappingProblem]) -> list[QubitMapping]:
		ids = [str(n) for n in range(len(problems))]
		answers = []
		for n, problem in enumerate(problems):
			ExportProblem(
				problem,
				AmplifyRuntimeSettings(
					self.token, self.timeout, self.constraint_strength, self.reduce_unused_qubits
				),
				ids[n]
			)
			answers.append(QubitMapping(problem.physicalDevice, problem.layers))

		with ThreadPoolExecutor(max_workers = self.max_num_machines) as pool:
			futures = [
				pool.submit(CallAmplifyRunner, n, ids[n])
				for n in range(len(problems))
			]
			for f in as_completed(futures):
				n = f.result()
				runtimeInfo = ImportResult(answers[n], ids[n])
				if(runtimeInfo.success == False):
					raise RuntimeError("failed at AmplifyRunner")
				
				if(self.constraint_strength < runtimeInfo.constraint_strength):
					self.constraint_strength = runtimeInfo.constraint_strength
					print("constraint_strength changed to " + str(self.constraint_strength))
		return answers