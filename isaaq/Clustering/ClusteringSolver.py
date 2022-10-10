from isaaq.Clustering.ClusterDeviceGenerator import GenerateClusterDevice
from isaaq.Clustering.ClusteringProblem import *

import random

class Cluster:
    def __init__(self, qubits: list[int] = [], totalSize: int = 0):
        self.qubits = qubits
        self.totalSize = totalSize
    
    def addQubit(self, q: int, size: int):
        self.qubits.append(q)
        self.totalSize += size

def RandomClustering(problem: ClusteringProblem) -> list[list[int]]:
    clusters: list[Cluster] = [Cluster() for i in range(problem.numClusters)]
    isChecked: list[bool] = [False for i in range(problem.originalDevice.qubits.N)]
    candidates: list[list[int]] = [[] for i in range(problem.originalDevice.qubits.N)]

    qubitList = []
    roots = random.sample(list(range(problem.originalDevice.qubits.N)), problem.numClusters)
    for i in range(problem.numClusters):
        root = roots[i]
        qubitList.append(root)
        candidates[root].append(i)
    
    i = 0
    while(i < len(qubitList)):
        x = qubitList[i]

        j, s = -1, problem.originalDevice.qubits.N + 1
        for _j in candidates[x]:
            if(clusters[_j].totalSize < s):
                j = _j
                s = clusters[j].totalSize
        clusters[j].addQubit(x, problem.originalDevice.qubits.sizes[x])
        isChecked[x] = True

        for y in problem.originalDevice.graph.neighbours[x]:
            if(isChecked[y]): continue
            if(len(candidates[y]) == 0): qubitList.append(y)
            candidates[y].append(j)

        i += 1

    print(qubitList)

    return  [cluster.qubits for cluster in clusters]

def SolveClusteringProblem(problem: ClusteringProblem) -> ClusteringResult:
    clusters = RandomClustering(problem)

    clusterDevice = GenerateClusterDevice(
        problem.originalDevice, clusters,
        lambda X, W: min(X)
    )
    
    return ClusteringResult(
        problem.originalDevice, clusterDevice, clusters
    )