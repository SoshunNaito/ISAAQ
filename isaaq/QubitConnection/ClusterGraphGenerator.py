import os

from isaaq.Common.PhysicalDevice import *
from isaaq.IO.PhysicalDevice import *

from typing import Callable

def GenerateClusterDevice(
    originalDevice: PhysicalDevice, clusteringResult: list[list[int]],
    clusterCostFunc: Callable[[list[float]], float]
) -> PhysicalDevice:

    clusterQubits = PhysicalQubits(len(clusteringResult), [len(A) for A in clusteringResult])
    qubitToCluster: list[int] = [-1] * originalDevice.qubits.numQubits
    for idx_c in range(len(clusteringResult)):
        for idx_q in clusteringResult[idx_c]:
            if(qubitToCluster[idx_q] != -1):
                raise RuntimeError("複数のqubitが同じclusterに属しています")
            qubitToCluster[idx_q] = idx_c
    for c in qubitToCluster:
        if(c == -1): raise RuntimeError("clusterに属さないqubitがあります")
    
    edges: set[Tuple[int, int]] = set()
    for _a, _b in originalDevice.graph.edges:
        a, b = qubitToCluster[_a], qubitToCluster[_b]
        if(a == b): continue
        if(a > b): a, b = b, a
        edges.add((a, b))

    cost_cnot: list[list[float]] = [[0 for j in range(clusterQubits.N)] for i in range(clusterQubits.N)]
    cost_swap: list[list[float]] = [[0 for j in range(clusterQubits.N)] for i in range(clusterQubits.N)]

    for i in range(clusterQubits.N):
        qubits_i = clusteringResult[i]
        for j in range(clusterQubits.N):
            qubits_j = clusteringResult[j]

            cnots, swaps = [], []
            for qi in qubits_i:
                for qj in qubits_j:
                    cnots.append(originalDevice.cost.cost_cnot[qi][qj])
                    swaps.append(originalDevice.cost.cost_swap[qi][qj])
            
            cost_cnot[i][j] = clusterCostFunc(cnots)
            cost_swap[i][j] = clusterCostFunc(swaps)

    clusterGraph = PhysicalDeviceGraph(originalDevice.graph.name + "_", clusterQubits.N, list(edges))
    clusterCost = PhysicalDeviceCost(originalDevice.cost.name + "_", cost_cnot, cost_swap)

    graphFolderPath = os.path.join(os.path.dirname(__file__), "../data/device_graph/" + clusterGraph.name)
    costFolderpath = os.path.join(os.path.dirname(__file__), "../data/device_cost/learned/" + clusterCost.name)
    costFilepath = os.path.join(costFolderpath, "cost_tables.txt")
    os.makedirs(graphFolderPath, exist_ok = True)
    os.makedirs(costFolderpath, exist_ok = True)

    ExportQubits(clusterQubits, clusterGraph.name)
    ExportGraph(clusterGraph, clusterGraph.name)
    ExportCost(costFilepath, clusterCost)
    return PhysicalDevice(clusterQubits, clusterGraph, clusterCost)