import os

from isaaq.Common.QuantumGates import *
from isaaq.Common.QuantumCircuit import *
from isaaq.Common.PhysicalDevice import *
from isaaq.Common.QubitMapping import *

from isaaq.Construct.SubModule.Placing import *
from isaaq.Construct.SubModule.Routing import *
from isaaq.Construct.SubModule.RoutingCache import *

def ConstructCircuit(
	circuit_src: QuantumCircuit, mapping: QubitMapping, routingCache: RoutingCache = None,
	addRoutingLog = True, showConstructLog = False
) -> QuantumCircuit:

	folderPath = os.path.join(os.path.dirname(__file__), "../internal_data/log/swap/actual/" + mapping.physicalDevice.cost.name)
	logFilePath = os.path.join(folderPath, "log.txt")
	logs = []
	routingCost, placingCost = 0, 0

	if(routingCache != None): cache = routingCache
	else: cache = RoutingCache(mapping.physicalDevice.graph)

	circuit_dst = QuantumCircuit([("Q", mapping.physicalDevice.qubits.N)], circuit_src.Cbits)
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

			if(showConstructLog):
				count = len(gates)
				routingCost += count
				print("(routing) " + str(count) + " CNOTs")

			if(addRoutingLog == True):
				log_str = str(len(gates)) + ": " + " ".join([str(n) for n in physicalToPhysical]) + "\n"
				logs.append(log_str)

		# placing gates
		layer = mapping.layers[l]
		gates = Placing(layer.virtualGates, layer.virtualToPhysical, mapping.physicalDevice.graph)
		for g in gates: circuit_dst.AddGate(g)

		if(showConstructLog):
			count = sum([1 if isinstance(gate, CXGate) else 0 for gate in gates])
			placingCost += count
			print("(placing) " + str(count) + " CNOTs")

	if(addRoutingLog == True):
		os.makedirs(folderPath, exist_ok = True)
		with open(logFilePath, "a") as f:
			f.writelines(logs)

	if(showConstructLog):
		print("placing cost = " + str(placingCost))
		print("routing cost = " + str(routingCost))

	return circuit_dst