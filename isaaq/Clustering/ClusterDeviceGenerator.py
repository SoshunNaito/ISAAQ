import os

from isaaq.Common.PhysicalDevice import *
from isaaq.IO.PhysicalDevice import *

from typing import Callable

def GenerateClusterDevice(
    originalDevice: PhysicalDevice, clusters: list[list[int]],
    clusterCostFunc: Callable[[list[float], list[float]], float]
) -> PhysicalDevice:

    clusterQubits = PhysicalQubits(len(clusters), [sum([originalDevice.qubits.sizes[c] for c in cluster]) for cluster in clusters])
    qubitToCluster: list[int] = [-1] * originalDevice.qubits.numQubits
    for idx_c in range(len(clusters)):
        for idx_q in clusters[idx_c]:
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
        qubits_i = clusters[i]
        for j in range(clusterQubits.N):
            qubits_j = clusters[j]

            cnots, swaps, weights = [], [], []
            for qi in qubits_i:
                for qj in qubits_j:
                    cnots.append(originalDevice.cost.cost_cnot[qi][qj])
                    swaps.append(originalDevice.cost.cost_swap[qi][qj])
                    weights.append(originalDevice.qubits.sizes[qi] * originalDevice.qubits.sizes[qj])
            
            cost_cnot[i][j] = clusterCostFunc(cnots, weights)
            cost_swap[i][j] = clusterCostFunc(swaps, weights)

    clusterGraph = PhysicalDeviceGraph(originalDevice.graph.name + "_", clusterQubits.N, list(edges))
    clusterCost = PhysicalDeviceCost(originalDevice.cost.name + "_", cost_cnot, cost_swap)

    costFolderpath = os.path.join(os.path.dirname(__file__), "../internal_data/device_cost/learned/" + clusterCost.name)
    costFilepath = os.path.join(costFolderpath, "cost_tables.txt")

    ExportQubits(clusterQubits, clusterGraph.name)
    ExportGraph(clusterGraph, clusterGraph.name)
    ExportCost(costFilepath, clusterCost)
    return PhysicalDevice(clusterQubits, clusterGraph, clusterCost)