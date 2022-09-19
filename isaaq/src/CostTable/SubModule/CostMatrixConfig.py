import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from isaaq.src.Common.PhysicalDevice import *
from typing import Tuple

class CostMatrixConfig:
    def __init__(self, N: int, vars: list[list[Tuple[int, int]]]):
        self.N = N
        self._registerVariables(vars)
    
    def _registerVariables(self, vars: list[list[Tuple[int, int]]]):
        self.edgeToVariable: list[int] = [len(vars)] * (self.N ** 2)
        self.variableToEdges: list[list[int]] = [[]]

        for n in range(len(vars)):
            edges = vars[n]
            for (a, b) in edges:
                idx = a * self.N + b
                if(self.edgeToVariable[idx] != len(vars)):
                    raise RuntimeError("変数が多重に定義されました")
                self.edgeToVariable[idx] = n

        for idx in range(len(self.edgeToVariable)):
            v = self.edgeToVariable[idx]
            while(len(self.variableToEdges) <= v):
                self.variableToEdges.append([])
            self.variableToEdges[v].append(idx)

    def __str__(self):
        return "Config_" + str(self.N) + "_" + str(len(self.variableToEdges))

class FullConnectedConfig(CostMatrixConfig):
    def __init__(self, N: int):
        vars = []
        for a in range(N):
            for b in range(N):
                vars.append([(a, b)])
        super().__init__(N, vars)

class LocallyConnectedConfig(CostMatrixConfig):
    def __init__(self, N: int, maxDist: int, graph: PhysicalDeviceGraph):
        vars: list[list[Tuple[int, int]]] = []
        for a in range(N):
            for b in range(N):
                if(graph.distanceTo[a][b] <= maxDist):
                    vars.append([(a, b)])

        V = len(vars) - 1
        for a in range(N):
            for b in range(N):
                if(graph.distanceTo[a][b] > maxDist):
                    v = V + graph.distanceTo[a][b] - maxDist
                    while(len(vars) <= v): vars.append([])
                    vars[v].append((a, b))
        super().__init__(N, vars)

def LoadCostMatrixConfig(filepath: str) -> CostMatrixConfig:
    with open(filepath, "r") as f:
        S = f.readlines()
    N = int(S[0].strip())
    S = S[1:]
    vars: list[list[Tuple[int, int]]] = []
    for s in S:
        idxList = [int(idx) for idx in s.strip().split(" ")]
        edges = [(idx // N, idx % N) for idx in idxList]
        vars.append(edges)
    return CostMatrixConfig(N, vars)

def SaveCostMatrixConfig(filepath: str, config: CostMatrixConfig):
    S = []
    S.append(str(config.N) + "\n")
    for idxList in config.variableToEdges:
        s = " ".join([str(idx) for idx in idxList]) + "\n"
        S.append(s)
    
    with open(filepath, "w") as f:
        f.writelines(S)