import typing
from isaaq.Clustering.ClusterDeviceGenerator import GenerateClusterDevice
from isaaq.Clustering.ClusteringProblem import *

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities, asyn_fluidc
from heapq import heappush, heappop
import random

from typing import Callable

# class Cluster:
#     def __init__(self, qubits: list[int] = [], totalSize: int = 0):
#         self.qubits = [q for q in qubits]
#         self.totalSize = totalSize
    
#     def addQubit(self, q: int, size: int):
#         self.qubits.append(q)
#         self.totalSize += size

# def RandomClustering(problem: ClusteringProblem) -> list[list[int]]:
#     clusters: list[Cluster] = [Cluster() for i in range(problem.numClusterDevices)]
#     isChecked: list[bool] = [False for i in range(problem.originalDevice.qubits.N)]
#     candidates: list[list[int]] = [[] for i in range(problem.originalDevice.qubits.N)]

#     qubitList = []
#     # roots = random.sample(list(range(problem.originalDevice.qubits.N)), problem.numClusterDevices)
#     islands = [
#         (problem.originalDevice.qubits.sizes[i] + random.random(), i)
#         for i in range(problem.originalDevice.qubits.N)
#     ]
#     roots = [i for (s, i) in sorted(islands, reverse=True)]

#     for i in range(problem.numClusterDevices):
#         root = roots[i]
#         qubitList.append(root)
#         candidates[root].append(i)
    
#     i = 0
#     while(i < len(qubitList)):
#         x = qubitList[i]

#         j, s = -1, problem.originalDevice.qubits.N + 1
#         for _j in candidates[x]:
#             if(clusters[_j].totalSize < s):
#                 j = _j
#                 s = clusters[j].totalSize
#         clusters[j].addQubit(x, problem.originalDevice.qubits.sizes[x])
#         isChecked[x] = True

#         for y in problem.originalDevice.graph.neighbours[x]:
#             if(isChecked[y]): continue
#             if(len(candidates[y]) == 0): qubitList.append(y)
#             candidates[y].append(j)
#         i += 1
#     return  [[q for q in cluster.qubits] for cluster in clusters]


# clusteringMethod:
# lambda G, n: RandomClustering(G, n),
# lambda G, n: asyn_fluidc(G, n),
# lambda G, n: greedy_modularity_communities(G, cutoff=n, best_n=n, resolution=n**0.5),

# clusterCostFunc:
# lambda values, weights: min(values)
# lambda values, weights: sum([values[i] * weights[i] for i in range(len(weights))]) / sum(weights)

def SolveClusteringProblem(
    problem: ClusteringProblem,
    clusteringMethod: Callable[[nx.Graph, int], list[list[int]]] =
        lambda G, n: [
            list(result) for result in greedy_modularity_communities(
                G, cutoff=n, best_n=n, resolution=n**0.5
            )
        ],
    clusterCostFunc: Callable[[list[float], list[float]], float] =
        lambda values, weights: min(values)
) -> ClusteringResult:

    symbols = [0 for i in range(problem.originalDevice.graph.N)]
    numClustersList = [int(problem.originalDevice.graph.N ** (i / problem.numClusterDevices)) for i in range(problem.numClusterDevices + 1)]

    clusteringResult = ClusteringResult(
        problem.numClusterDevices,
        [None for i in range(problem.numClusterDevices)],
        [[] for i in range(problem.numClusterDevices)],
    )
    for device_idx in range(problem.numClusterDevices):
        parentSize = [0] * numClustersList[device_idx]
        childCount = [1] * numClustersList[device_idx]
        for i in range(problem.originalDevice.graph.N):
            parentSize[symbols[i]] += 1

        print("device_idx = " + str(device_idx))

        # parentSizeに応じてchildCountを決定する
        heap = []
        for c in range(numClustersList[device_idx]):
            heappush(heap, (childCount[c] / parentSize[c], c))
        for j in range(numClustersList[device_idx], numClustersList[device_idx + 1]):
            (_, c) = heappop(heap)
            childCount[c] += 1
            heappush(heap, (childCount[c] / parentSize[c], c))

        # 各parentに対してクラスタリングを適用する
        child_idx = 0
        nextSymbols = [0 for i in range(problem.originalDevice.graph.N)]
        lenList = []
        elapsedTime = 0
        for c in range(numClustersList[device_idx]):
            G = nx.Graph()
            for i in range(problem.originalDevice.graph.N):
                if(symbols[i] == c): G.add_node(i)
            for (u, v) in problem.originalDevice.graph.edges:
                if(symbols[u] == c and symbols[v] == c): G.add_edge(u, v)
            
            results = clusteringMethod(G, childCount[c])
            for result in results: lenList.append(len(result))
            
            for i in range(childCount[c]):
                for n in results[i]: nextSymbols[n] = child_idx
                child_idx += 1

        if(device_idx == problem.numClusterDevices - 1): nextSymbols = list(range(len(nextSymbols)))

        clusterMappings = [set() for _ in range(numClustersList[device_idx])]
        for n in range(problem.originalDevice.graph.N): clusterMappings[symbols[n]].add(nextSymbols[n])
        for clusterMapping in clusterMappings: clusteringResult.clusterMappings[device_idx].append(list(clusterMapping))
    
    clusteringResult.clusterDevices[problem.numClusterDevices - 1] = problem.originalDevice
    for i in range(problem.numClusterDevices - 1)[::-1]:
        clusteringResult.clusterDevices[i] = GenerateClusterDevice(
            clusteringResult.clusterDevices[i+1], clusteringResult.clusterMappings[i+1],
            clusterCostFunc
        )
    
    return clusteringResult