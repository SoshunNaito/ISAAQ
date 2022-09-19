import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from isaaq.src.Common.PhysicalDevice import *
from isaaq.src.CostTable.SubModule.SwapCostMatrix import *
from isaaq.src.CostTable.CostMatrixGenerator import *

import numpy as np

def _GenerateCostTable(costMatrix: SwapCostMatrix) -> list[list[float]]:
    # normalize each row
    for idx in range(costMatrix.numvars):
        if(abs(costMatrix.frequency[idx, idx]) < 0.00001):
            rate = 1
        else:
            rate = 1.0 / costMatrix.frequency[idx, idx]
        costMatrix.frequency[idx, :] *= rate
        costMatrix.swapCost[idx] *= rate

    U, S, V_t = np.linalg.svd(np.array(costMatrix.frequency), full_matrices = False)

    # print("N = " + str(costMatrix.numvars))
    # print("N_samples = " + str(costMatrix.numSamples))
    # print(U.shape)
    # print(S.shape)
    # print(V_t.shape)

    while(S[-1] < 0.00000001): S = S[:-1]
    r = len(S)
    # print("rank = " + str(r))

    U = U[:, :r]
    S = np.diag(S)
    V_t = V_t[:r, :]

    B = U
    C = S @ V_t

    A2_inv = C.T @ np.linalg.inv(C @ C.T) @ np.linalg.inv(B.T @ B) @ B.T
    X = A2_inv @ costMatrix.swapCost

    ans = [[0.0 for i in range(costMatrix.N)] for j in range(costMatrix.N)]
    for i in range(costMatrix.N):
        for j in range(costMatrix.N):
            idx = i * costMatrix.N + j
            ans[i][j] = X[costMatrix.config.edgeToVariable[idx]]
    return ans

def GenerateInitialDeviceCost(
    deviceCostName: str, graph: PhysicalDeviceGraph,
    use_cache = True,
    maxLocalInteractionDist = -1
) -> PhysicalDeviceCost:
    cost_cnot = [
        [
            max(1, (graph.distanceTo[i][j] - 1) * 4)
            for j in range(graph.N)
        ]
        for i in range(graph.N)
    ]
    matrix = GenerateInitialCostMatrix(
        deviceCostName, graph, use_cache, maxLocalInteractionDist
    )
    cost_swap = _GenerateCostTable(matrix)

    deviceCost = PhysicalDeviceCost(deviceCostName, cost_cnot, cost_swap)
    return deviceCost

def GenerateLearnedDeviceCost(
    deviceCostName: str, graph: PhysicalDeviceGraph,
    use_cache = True,
    maxLocalInteractionDist = -1
) -> PhysicalDeviceCost:
    cost_cnot = [
        [
            max(1, (graph.distanceTo[i][j] - 1) * 4)
            for j in range(graph.N)
        ]
        for i in range(graph.N)
    ]

    initialCostMatrix = GenerateInitialCostMatrix(
        deviceCostName, graph, True, maxLocalInteractionDist
    )
    actualCostMatrix = GenerateActualCostMatrix(
        deviceCostName, graph, use_cache, maxLocalInteractionDist
    )
    matrix = initialCostMatrix + actualCostMatrix
    cost_swap = _GenerateCostTable(matrix)

    deviceCost = PhysicalDeviceCost(deviceCostName, cost_cnot, cost_swap)
    return deviceCost