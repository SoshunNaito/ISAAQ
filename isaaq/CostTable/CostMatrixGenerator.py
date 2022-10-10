import os

from isaaq.Common.PhysicalDevice import *
from isaaq.CostTable.SubModule.RandomPermutationGenerator import *
from isaaq.CostTable.SubModule.SwapCostMatrix import *
from isaaq.CostTable.SubModule.CostMatrixConfig import *
from isaaq.Construct.SubModule.Routing import *
from isaaq.Construct.SubModule.RoutingCache import *

def _GenerateConfig(graph: PhysicalDeviceGraph, maxLocalInteractionDist = -1) -> CostMatrixConfig:
	if(maxLocalInteractionDist == -1):
		config = FullConnectedConfig(graph.N)
		for d in range(1, 5)[::-1]:
			if(len(config.variableToEdges) > 1000):
				config = LocallyConnectedConfig(graph.N, d, graph)
	else:
		config = LocallyConnectedConfig(graph.N, maxLocalInteractionDist, graph)
	return config

def _GenerateInitialLog(filepath_log: str, graph: PhysicalDeviceGraph):
	routingCache = RoutingCache(graph)
	permutations = GenerateRandomPermutationList(graph.N, 4000000)

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

	folderPath = os.path.join(os.path.dirname(__file__), "../internal_data/log/swap/initial/" + deviceCostName)
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

	folderPath = os.path.join(os.path.dirname(__file__), "../internal_data/log/swap/actual/" + deviceCostName)
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