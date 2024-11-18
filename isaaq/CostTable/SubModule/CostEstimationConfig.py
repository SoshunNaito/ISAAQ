from isaaq.Common.PhysicalDevice import *
from typing import Callable, Tuple

class CostEstimationConfig:
    def __init__(self, N: int, coefs: list[list[float]], name = ""):
        self.N = N
        self.numvars = len(coefs[0])
        self.coefs = [[c for c in row] for row in coefs]
        if(len(coefs) != N ** 2):
            raise RuntimeError("係数行列のサイズが正しくありません")
        
        if(name == ""): name = "Config_" + str(self.N) + "_" + str(self.numvars)
        self.name = name

    def __str__(self): return self.name

# for small devices (N <= 10)
class FullConnectedConfig(CostEstimationConfig):
    def __init__(self, N: int):
        coefs = []
        for a in range(N ** 2):
            coefs.append([0 for b in range(N ** 2)])
            coefs[-1][a] = 1
        super().__init__(
            N, coefs,
            name = "Config_Full_" + str(N) + "_" + str(N ** 2)
        )
    
    @classmethod
    def GenerateFromGraph(cls, graph: PhysicalDeviceGraph):
        return cls(graph.N)

# for large devices (N <= 1000)
class CommonFunctionConfig(CostEstimationConfig):
    def __init__(self, N: int, func: Callable[[int, int], list[float]]):
        coefs = []
        for a in range(N):
            for b in range(N):
                coefs.append(func(a, b))
        super().__init__(
            N, coefs,
            name = "Config_Func_" + str(N) + "_" + str(len(coefs[0]))
        )
    
    @classmethod
    def GenerateFromGraph(
        cls, graph: PhysicalDeviceGraph,
        func: Callable[[PhysicalDeviceGraph, int, int], list[float]] = None
    ):
        if(func == None): func = lambda G, a, b: [G.distanceTo[a][b], 1]
        return cls(graph.N, lambda a, b: func(graph, a, b))

def LoadCostEstimationConfig(filepath: str) -> CostEstimationConfig:
    with open(filepath, "r") as f:
        S = f.readlines()
    N = int(S[0].strip())
    name = int(S[1].strip())

    S = S[2:]
    coefs: list[list[float]] = []
    for s in S:
        row = [float(x) for x in s.strip().split(" ")]
        coefs.append(row)
    return CostEstimationConfig(N, coefs, name)

def SaveCostEstimationConfig(filepath: str, config: CostEstimationConfig):
    S = []
    S.append(str(config.N) + "\n")
    S.append(str(config.name) + "\n")
    for row in config.coefs:
        s = " ".join([str(x) for x in row]) + "\n"
        S.append(s)
    
    with open(filepath, "w") as f:
        f.writelines(S)