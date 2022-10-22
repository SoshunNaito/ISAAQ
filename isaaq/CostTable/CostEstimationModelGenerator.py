import os

from isaaq.Common.PhysicalDevice import *
from isaaq.CostTable.SubModule.RandomPermutationGenerator import *
from isaaq.CostTable.SubModule.CostEstimationModel import *
from isaaq.CostTable.SubModule.CostEstimationConfig import *
from isaaq.Construct.SubModule.Routing import *
from isaaq.Construct.SubModule.RoutingCache import *

def _GenerateConfig(graph: PhysicalDeviceGraph) -> CostEstimationConfig:
	if(graph.N <= 20):
		config = FullConnectedConfig(graph.N)
	elif(graph.N <= 50):
		config = None
		for d in range(-1, 6)[::-1]:
			config = LocallyConnectedConfig(graph.N, d, graph)
			if((graph.N ** 2) * len(config.numvars) <= 200000): break
	else:
		meanDist = 0
		for a in range(graph.N):
			for b in range(graph.N):
				d = graph.distanceTo[a][b]
				meanDist += d
		meanDist /= (graph.N ** 2)

		config = CommonFunctionConfig(
			graph.N,
			lambda a, b: [
				graph.distanceTo[a][b] / meanDist,
				1,
				1 / (graph.distanceTo[a][b] + 1)
			]
		)
	return config

def _GenerateInitialLog(filepath_log: str, graph: PhysicalDeviceGraph, num_samples: int):
	routingCache = RoutingCache(graph)
	permutations = GenerateRandomPermutationList(graph.N, num_samples)

	S = []
	for p in permutations:
		cost = len(Routing(p, graph, routingCache))
		S.append(str(cost) + ": " + " ".join([str(n) for n in p]) + "\n")
	with open(filepath_log, "w") as f:
		f.writelines(S)

def GenerateInitialCostEstimationModel(
	deviceCostName: str, graph: PhysicalDeviceGraph,
	use_cache = True
) -> CostEstimationModel:

	config = _GenerateConfig(graph)

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
		costEstimationModel = LoadCostEstimationModelCache(filepath_cache)
	else:
		if(os.path.isfile(filepath_log) == False):
			_GenerateInitialLog(
				filepath_log, graph,
				num_samples = min(config.numvars * 20, 4000000 // (graph.N ** 2))
			)
		costEstimationModel = LoadCostEstimationModelFromFile(filepath_log, config)
		SaveCostEstimationModelCache(filepath_cache, costEstimationModel)
	
	return costEstimationModel

def GenerateActualCostEstimationModel(
	deviceCostName: str, graph: PhysicalDeviceGraph,
	use_cache = True
) -> CostEstimationModel:

	config = _GenerateConfig(graph)

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
		costEstimationModel = LoadCostEstimationModelCache(filepath_cache)
	else:
		costEstimationModel = CostEstimationModel(config)
		if(os.path.isfile(filepath_cache) and os.path.isfile(filepath_cache_config)):
			costEstimationModel = LoadCostEstimationModelCache(filepath_cache)
			if(str(costEstimationModel.config) != str(config)):
				costEstimationModel = CostEstimationModel(config)
		
		if(os.path.isfile(filepath_log) == False):
			raise RuntimeError("No log file found")
		costEstimationModel = costEstimationModel + LoadCostEstimationModelFromFile(filepath_log, config, costEstimationModel.numSamples)
		SaveCostEstimationModelCache(filepath_cache, costEstimationModel)
	
	return costEstimationModel