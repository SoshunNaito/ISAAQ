import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from Common.PhysicalDevice import *
from CostTable.SubModule.RandomPermutationGenerator import *
from CostTable.SubModule.SwapCostMatrix import *
from CostTable.SubModule.CostMatrixConfig import *
from Construct.SubModule.Routing import *
from Construct.SubModule.RoutingCache import *

def _GenerateConfig(graph: PhysicalDeviceGraph, maxLocalInteractionDist = -1) -> CostMatrixConfig:
	if(maxLocalInteractionDist == -1):
		config = FullConnectedConfig(graph.N)
	else:
		config = LocallyConnectedConfig(graph.N, maxLocalInteractionDist, graph)
	return config

def _GenerateInitialLog(filepath_log: str, graph: PhysicalDeviceGraph):
	routingCache = RoutingCache(graph)
	permutations = GenerateRandomPermutationList(graph.N, 10000)

	S = []
	for p in permutations:
		cost = len(Routing(p, graph, routingCache))
		S.append(str(cost) + ": " + " ".join([str(n) for n in p]) + "\n")
	with open(filepath_log, "w") as f:
		f.writelines(S)

def GenerateInitialCostMatrix(
	deviceCostName: str, graph: PhysicalDeviceGraph,
	use_cache = True,
	maxLocalInteractionDist = -1
) -> SwapCostMatrix:

	config = _GenerateConfig(graph, maxLocalInteractionDist)

	folderPath = os.path.join(os.path.dirname(__file__), "../../../data/log/swap/initial/" + deviceCostName)
	cacheFolderPath = os.path.join(folderPath, str(config))
	os.makedirs(folderPath, exist_ok = True)
	os.makedirs(cacheFolderPath, exist_ok = True)

	filepath_log = folderPath + "/log.txt"
	filepath_cache = os.path.join(cacheFolderPath, "cache.txt")
	filepath_cache_config = os.path.join(cacheFolderPath, "config.txt")

	if(
		use_cache == True and
		os.path.isfile(filepath_cache) and
		os.path.isfile(filepath_cache_config)
	):
		matrix = LoadSwapCostMatrixCache(filepath_cache)
	else:
		if(os.path.isfile(filepath_log) == False):
			_GenerateInitialLog(filepath_log, graph)
		matrix = LoadSwapCostMatrixFromFile(filepath_log, config)
		SaveSwapCostMatrixCache(filepath_cache, matrix)
	
	return matrix

def GenerateActualCostMatrix(
	deviceCostName: str, graph: PhysicalDeviceGraph,
	use_cache = True,
	maxLocalInteractionDist = -1
) -> SwapCostMatrix:

	config = _GenerateConfig(graph, maxLocalInteractionDist)

	folderPath = os.path.join(os.path.dirname(__file__), "../../../data/log/swap/actual/" + deviceCostName)
	cacheFolderPath = os.path.join(folderPath, str(config))
	os.makedirs(folderPath, exist_ok = True)
	os.makedirs(cacheFolderPath, exist_ok = True)

	filepath_log = folderPath + "/log.txt"
	filepath_cache = os.path.join(cacheFolderPath, "cache.txt")
	filepath_cache_config = os.path.join(cacheFolderPath, "config.txt")

	if(
		use_cache == True and
		os.path.isfile(filepath_cache) and
		os.path.isfile(filepath_cache_config)
	):
		matrix = LoadSwapCostMatrixCache(filepath_cache)
	else:
		matrix = SwapCostMatrix(config)
		if(os.path.isfile(filepath_cache) and os.path.isfile(filepath_cache_config)):
			matrix = LoadSwapCostMatrixCache(filepath_cache)
			if(str(matrix.config) != str(config)):
				matrix = SwapCostMatrix(config)
		
		if(os.path.isfile(filepath_log) == False):
			raise RuntimeError("No log file found")
		matrix = matrix + LoadSwapCostMatrixFromFile(filepath_log, config, matrix.numSamples)
		SaveSwapCostMatrixCache(filepath_cache, matrix)
	
	return matrix