import os

from isaaq.Common.PhysicalQubits import *
from isaaq.Common.PhysicalDevice import *
from isaaq.CostTable import *

def ImportQubits(deviceGraphName: str, filepath: str = "") -> PhysicalQubits:
	if(filepath == ""):
		filepath = os.path.join(os.path.dirname(__file__), "../internal_data/device_graph/" + deviceGraphName + "/qubits.txt")
	with open(filepath, mode = "r") as f:
		S = f.readlines()
	N = int(S[0].strip())
	sizes = [int(s) for s in S[1].strip().split()]
	return PhysicalQubits(N, sizes)

def ExportQubits(qubits: PhysicalQubits, deviceGraphName: str, filepath: str = ""):
	S = []
	S.append(str(qubits.N) + "\n")
	S.append(" ".join([str(s) for s in qubits.sizes]) + "\n")

	if(filepath == ""):
		filepath = os.path.join(os.path.dirname(__file__), "../internal_data/device_graph/" + deviceGraphName + "/qubits.txt")
	
	os.makedirs(os.path.dirname(filepath), exist_ok = True)
	with open(filepath, "w") as f:
		f.writelines(S)

def ImportGraph(deviceGraphName: str, filepath: str = "") -> PhysicalDeviceGraph:
	if(filepath == ""):
		filepath = os.path.join(os.path.dirname(__file__), "../internal_data/device_graph/" + deviceGraphName + "/edges.txt")
	with open(filepath, mode = "r") as f:
		S = f.readlines()
	N, M = map(int, S[0].strip().split())
	S = S[1:]

	edges = []
	for m in range(M):
		a, b = map(int, S[m].strip().split())
		edges.append((a, b))
	return PhysicalDeviceGraph(deviceGraphName, N, edges)

def ExportGraph(graph: PhysicalDeviceGraph, deviceGraphName: str, filepath: str = ""):
	S = []
	S.append(str(graph.N) + " " + str(len(graph.edges)) + "\n")
	for a, b in graph.edges:
		S.append(str(a) + " " + str(b) + "\n")

	if(filepath == ""):
		filepath = os.path.join(os.path.dirname(__file__), "../internal_data/device_graph/" + deviceGraphName + "/edges.txt")

	os.makedirs(os.path.dirname(filepath), exist_ok = True)
	with open(filepath, "w") as f:
		f.writelines(S)

def ImportCost(deviceCostName: str, filepath: str) -> PhysicalDeviceCost:
	with open(filepath, mode = "r") as f:
		S = f.readlines()
	N = int(S[0].strip())
	S = S[1:]

	cost_cnot = []
	for i in range(N):
		cost_cnot.append([float(a) for a in S[i].strip().split()])
	S = S[N:]

	cost_swap = []
	for i in range(N):
		cost_swap.append([float(a) for a in S[i].strip().split()])

	return PhysicalDeviceCost(deviceCostName, cost_cnot, cost_swap)

def ExportCost(filepath: str, deviceCost: PhysicalDeviceCost):
	S = []
	S.append(str(len(deviceCost.cost_cnot)) + "\n")
	for costs in deviceCost.cost_cnot:
		S.append(" ".join([str(c) for c in costs]) + "\n")
	for costs in deviceCost.cost_swap:
		S.append(" ".join([str(c) for c in costs]) + "\n")
	
	os.makedirs(os.path.dirname(filepath), exist_ok = True)
	with open(filepath, "w") as f:
		f.writelines(S)

def PrepareCost(deviceGraphName: str, deviceCostName: str, refreshCostTable: bool) -> PhysicalDeviceCost:
	folderPath_initial = os.path.join(os.path.dirname(__file__), "../internal_data/device_cost/initial/" + deviceCostName)
	folderPath_learned = os.path.join(os.path.dirname(__file__), "../internal_data/device_cost/learned/" + deviceCostName)
	filepath_initial = os.path.join(folderPath_initial, "cost_tables.txt")
	filepath_learned = os.path.join(folderPath_learned, "cost_tables.txt")

	if(refreshCostTable == False):
		if(os.path.isfile(filepath_learned)):
			return ImportCost(deviceCostName, filepath_learned)
		elif(os.path.isfile(filepath_initial)):
			return ImportCost(deviceCostName, filepath_initial)

	try:
		graph = ImportGraph(deviceGraphName)
		deviceCost = GenerateLearnedDeviceCost(deviceCostName, graph, ~refreshCostTable, -1)

		ExportCost(filepath_learned, deviceCost)
		return deviceCost
	except:
		graph = ImportGraph(deviceGraphName)
		deviceCost = GenerateInitialDeviceCost(deviceCostName, graph, ~refreshCostTable, -1)
		
		ExportCost(filepath_initial, deviceCost)
		return deviceCost

def ImportDeviceManually(deviceGraphName: str, deviceCostName: str, refreshCostTable: bool) -> PhysicalDevice:
	graph = ImportGraph(deviceGraphName)
	cost = PrepareCost(deviceGraphName, deviceCostName, refreshCostTable)

	try:
		qubits = ImportQubits(deviceGraphName)
	except:
		qubits = PhysicalQubits(graph.N)
		ExportQubits(qubits, graph.name)
	return PhysicalDevice(qubits, graph, cost)

def ImportDevice(deviceName: str, refreshCostTable: bool = False) -> PhysicalDevice:
	return ImportDeviceManually(deviceName, deviceName, refreshCostTable)