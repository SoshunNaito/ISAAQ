import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from CostTable.SubModule.CostMatrixConfig import *

import numpy as np
from nptyping import *
from typing import *

class SwapCostMatrix:
	def __init__(self, config: CostMatrixConfig):
		self.N = config.N
		self.config = config
		self.numvars = len(self.config.variableToEdges)
		self.numSamples = 0
		
		self.frequency = np.zeros((self.numvars, self.numvars))
		self.swapCost = np.zeros(self.numvars)

	def Add(self, permutation: list[int], cost: int):
		v1: list[Tuple(int, int)] = []
		v2: list[Tuple(int, int)] = []

		for a in range(len(permutation)):
			b = permutation[a]
			v1.append(self.config.edgeToVariable[a * self.N + b])
			v2.append(self.config.edgeToVariable[b * self.N + a])

		# 対称性を確保するため、逆方向の置換もサンプルに加える
		for v in [v1, v2]:
			for idx1 in v:
				self.swapCost[idx1] += cost
				for idx2 in v:
					self.frequency[idx1, idx2] += 1

		self.numSamples += 2

	def __add__(self, other):
		if(isinstance(other, SwapCostMatrix)):
			if(str(self.config) == str(other.config)):
				matrix = SwapCostMatrix(self.config)

				matrix.frequency = self.frequency + other.frequency
				matrix.swapCost = self.swapCost + other.swapCost
				matrix.numSamples = self.numSamples + other.numSamples
				return matrix
			else:
				raise RuntimeError("config is different")
		else:
			raise RuntimeError("addition with " + str(other) + " is not supported")

	def __mul__(self, param):
		if(isinstance(param, int) or isinstance(param, float)):
			matrix = SwapCostMatrix(self.config)

			matrix.frequency = self.frequency * param
			matrix.swapCost = self.swapCost * param
			matrix.numSamples = self.numSamples * param
			return matrix
		else:
			raise RuntimeError("mulplication with " + str(param) + " is not supported")

def LoadSwapCostMatrixFromFile(filepath: str, config: CostMatrixConfig, lineOffset: int = 0) -> SwapCostMatrix:
	with open(filepath, "r") as f:
		S = f.readlines()

	costMatrix = SwapCostMatrix(config)
	if(lineOffset < len(S)):
		for s in S[lineOffset:]:
			s = s.replace(":", "")
			A = [int(a) for a in s.split(" ")]
			cost, A = A[0], A[1:]
			costMatrix.Add(A, cost)
	return costMatrix

def SaveSwapCostMatrixCache(filepath: str, matrix: SwapCostMatrix):
	filepath_config = filepath.replace(".txt", ".config")
	SaveCostMatrixConfig(filepath_config, matrix.config)

	S = []
	S.append(str(matrix.numvars) + " " + str(matrix.numSamples) + "\n")
	S.append(" ".join([str(matrix.swapCost[a]) for a in range(matrix.numvars)]) + "\n")
	for a in range(matrix.numvars):
		S.append(" ".join([str(matrix.frequency[(a, b)]) for b in range(matrix.numvars)]) + "\n")

	with open(filepath, "w") as f:
		f.writelines(S)

def LoadSwapCostMatrixCache(filepath: str) -> SwapCostMatrix:
	filepath_config = filepath.replace(".txt", ".config")
	config = LoadCostMatrixConfig(filepath_config)
	matrix = SwapCostMatrix(config)

	with open(filepath, "r") as f:
		S = f.readlines()

	A = S[0].strip().split(" ")
	matrix.numvars, matrix.numSamples = int(A[0]), int(A[1])

	A = S[1].strip().split(" ")
	S = S[2:]
	for n in range(matrix.numvars):
		matrix.swapCost[n] = int(A[n])

	for a in range(matrix.numvars):
		F = S[a].strip().split(" ")
		for b in range(matrix.numvars):
			matrix.frequency[(a, b)] = int(F[b])
	
	return matrix