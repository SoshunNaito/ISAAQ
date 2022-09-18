import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from Common.QuantumGates import *
from Common.QuantumCircuit import *
from Common.PhysicalDevice import *
from Common.QubitMapping import *

from Construct.SubModule.Placing import *
from Construct.SubModule.Routing import *
from Construct.SubModule.RoutingCache import *



def ConstructCircuit(
	circuit_src: QuantumCircuit, mapping: QubitMapping,
	addRoutingLog = True, routingCache: RoutingCache = None
) -> QuantumCircuit:

	folderPath = os.path.join(os.path.dirname(__file__), "../../../data/log/swap/actual/" + mapping.physicalDevice.cost.name)
	logFilePath = os.path.join(folderPath, "log.txt")
	logs = []

	if(routingCache != None): cache = routingCache
	else: cache = RoutingCache(mapping.physicalDevice.graph)

	circuit_dst = QuantumCircuit(circuit_src.Qubits, circuit_src.Cbits)
	for l in range(mapping.numLayers):
		# routing Qubits
		if(l > 0):
			virtualToPhysical_old = mapping.layers[l-1].virtualToPhysical
			virtualToPhysical_new = mapping.layers[l].virtualToPhysical
			physicalToPhysical = [-1] * mapping.physicalDevice.qubits.N
			for i in range(len(virtualToPhysical_old)):
				physicalToPhysical[virtualToPhysical_old[i]] = virtualToPhysical_new[i]

			gates = Routing(physicalToPhysical, mapping.physicalDevice.graph, cache)
			for g in gates: circuit_dst.AddGate(g)

			if(addRoutingLog == True):
				log_str = str(len(gates)) + ": " + " ".join([str(n) for n in physicalToPhysical]) + "\n"
				logs.append(log_str)

		# placing gates
		layer = mapping.layers[l]
		gates = Placing(layer.virtualGates, layer.virtualToPhysical, mapping.physicalDevice.graph)
		for g in gates: circuit_dst.AddGate(g)

	if(addRoutingLog == True):
		os.makedirs(folderPath, exist_ok = True)
		with open(logFilePath, "a") as f:
			f.writelines(logs)

	return circuit_dst