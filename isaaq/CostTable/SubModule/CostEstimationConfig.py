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

# for small devices (N <= 20)
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

# for medium devices (N <= 50)
class LocallyConnectedConfig(CostEstimationConfig):
    def __init__(self, N: int, maxDist: int, graph: PhysicalDeviceGraph):
        if(maxDist < -1):
            print("LocallyConnectedConfig: maxDist cannot be smaller than -1")
            maxDist = -1

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

        coefs = [[0 for v in range(len(vars))] for n in range(N ** 2)]
        for v in range(len(vars)):
            for (a, b) in vars[v]:
                idx = a * N + b
                coefs[idx][v] = 1
                
        super().__init__(
            N, coefs,
            name = "Config_Local_" + str(N) + "_" + str(len(vars))
        )

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