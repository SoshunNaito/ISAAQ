import numpy as np
from typing import Tuple

from isaaq.CostTable.SubModule.CostEstimationConfig import *

class CostEstimationModel:
	def __init__(self, config: CostEstimationConfig):
		self.N = config.N
		self.config = config
		self.numvars = self.config.numvars
		self.numSamples = 0
		
		self.frequency = np.zeros((self.numvars, self.numvars))
		self.swapCost = np.zeros(self.numvars)

	def Add(self, permutation: list[int], cost: int):
		v1: list[Tuple(int, float)] = []
		v2: list[Tuple(int, float)] = []

		for a in range(len(permutation)):
			b = permutation[a]
			if(b == -1): continue
			v1.append((a * self.N + b, 1))
			v2.append((b * self.N + a, 1))

		# 対称性を確保するため、逆方向の置換もサンプルに加える
		for v in [v1, v2]:
			dc = np.zeros(self.numvars)
			for idx, weight in v:
				dc += np.array(self.config.coefs[idx]) * weight

			self.frequency += dc.reshape(self.numvars, 1) @ dc.reshape(1, self.numvars)
			self.swapCost += cost * dc

		self.numSamples += 2

	def __add__(self, other):
		if(isinstance(other, CostEstimationModel)):
			if(str(self.config) == str(other.config)):
				costEstimationModel = CostEstimationModel(self.config)

				costEstimationModel.frequency = self.frequency + other.frequency
				costEstimationModel.swapCost = self.swapCost + other.swapCost
				costEstimationModel.numSamples = self.numSamples + other.numSamples
				return costEstimationModel
			else:
				raise RuntimeError("config is different")
		else:
			raise RuntimeError("addition with " + str(other) + " is not supported")

	def __mul__(self, param):
		if(isinstance(param, int) or isinstance(param, float)):
			costEstimationModel = CostEstimationModel(self.config)

			costEstimationModel.frequency = self.frequency * param
			costEstimationModel.swapCost = self.swapCost * param
			costEstimationModel.numSamples = self.numSamples * param
			return costEstimationModel
		else:
			raise RuntimeError("mulplication with " + str(param) + " is not supported")

def LoadCostEstimationModelFromFile(filepath: str, config: CostEstimationConfig, lineOffset: int = 0) -> CostEstimationModel:
	with open(filepath, "r") as f:
		S = f.readlines()

	costEstimationModel = CostEstimationModel(config)
	if(lineOffset < len(S)):
		for s in S[lineOffset:]:
			s = s.replace(":", "")
			A = [int(a) for a in s.split(" ")]
			cost, A = A[0], A[1:]
			costEstimationModel.Add(A, cost)
	return costEstimationModel

def SaveCostEstimationModelCache(filepath: str, costEstimationModel: CostEstimationModel):
	filepath_config = filepath.replace(".txt", ".config")
	SaveCostEstimationConfig(filepath_config, costEstimationModel.config)

	S = []
	S.append(str(costEstimationModel.numvars) + " " + str(costEstimationModel.numSamples) + "\n")
	S.append(" ".join([str(costEstimationModel.swapCost[a]) for a in range(costEstimationModel.numvars)]) + "\n")
	for a in range(costEstimationModel.numvars):
		S.append(" ".join([str(costEstimationModel.frequency[(a, b)]) for b in range(costEstimationModel.numvars)]) + "\n")

	with open(filepath, "w") as f:
		f.writelines(S)

def LoadCostEstimationModelCache(filepath: str) -> CostEstimationModel:
	filepath_config = filepath.replace(".txt", ".config")
	config = LoadCostEstimationConfig(filepath_config)
	costEstimationModel = CostEstimationModel(config)

	with open(filepath, "r") as f:
		S = f.readlines()

	A = S[0].strip().split(" ")
	costEstimationModel.numvars, costEstimationModel.numSamples = int(A[0]), int(A[1])

	A = S[1].strip().split(" ")
	S = S[2:]
	for n in range(costEstimationModel.numvars):
		costEstimationModel.swapCost[n] = int(A[n])

	for a in range(costEstimationModel.numvars):
		F = S[a].strip().split(" ")
		for b in range(costEstimationModel.numvars):
			costEstimationModel.frequency[(a, b)] = int(F[b])
	
	return costEstimationModel