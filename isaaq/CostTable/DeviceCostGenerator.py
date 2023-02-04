import numpy as np

from isaaq.Common.PhysicalDevice import *
from isaaq.CostTable.SubModule.CostEstimationModel import *
from isaaq.CostTable.CostEstimationModelGenerator import *

def _GenerateCostTable(costEstimationModel: CostEstimationModel) -> list[list[float]]:
    frequency = np.zeros((costEstimationModel.numvars, costEstimationModel.numvars))
    swapCost = np.zeros(costEstimationModel.numvars)

    frequency += costEstimationModel.frequency
    swapCost += costEstimationModel.swapCost

    # normalize each row
    for idx in range(costEstimationModel.numvars):
        if(abs(frequency[idx, idx]) < 0.00001):
            rate = 1
        else:
            rate = 1.0 / frequency[idx, idx]
        frequency[idx, :] *= rate
        swapCost[idx] *= rate

    U, S, V_t = np.linalg.svd(np.array(frequency), full_matrices = False)

    # print("N = " + str(costEstimationModel.numvars))
    # print("N_samples = " + str(costEstimationModel.numSamples))
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
    X = A2_inv @ swapCost

    ans = [[0.0 for i in range(costEstimationModel.N)] for j in range(costEstimationModel.N)]
    for i in range(costEstimationModel.N):
        for j in range(costEstimationModel.N):
            idx = i * costEstimationModel.N + j
            for n in range(costEstimationModel.numvars):
                ans[i][j] += costEstimationModel.config.coefs[idx][n] * X[n]
    return ans

def GenerateInitialDeviceCost(
    deviceCostName: str, graph: PhysicalDeviceGraph,
    config: CostEstimationConfig = None, use_cache = True
) -> PhysicalDeviceCost:

    cost_cnot = [
        [
            max(1, (graph.distanceTo[i][j] - 1) * 4)
            for j in range(graph.N)
        ]
        for i in range(graph.N)
    ]
    costEstimationModel = GenerateInitialCostEstimationModel(
        deviceCostName, graph, config, use_cache
    )
    cost_swap = _GenerateCostTable(costEstimationModel)

    deviceCost = PhysicalDeviceCost(deviceCostName, cost_cnot, cost_swap)
    return deviceCost

def GenerateLearnedDeviceCost(
    deviceCostName: str, graph: PhysicalDeviceGraph,
    config: CostEstimationConfig = None, use_cache = True
) -> PhysicalDeviceCost:

    cost_cnot = [
        [
            max(1, (graph.distanceTo[i][j] - 1) * 4)
            for j in range(graph.N)
        ]
        for i in range(graph.N)
    ]

    initialCostEstimationModel = GenerateInitialCostEstimationModel(
        deviceCostName, graph, config, True
    )
    learnedCostEstimationModel = GenerateLearnedCostEstimationModel(
        deviceCostName, graph, config, use_cache
    )
    costEstimationModel = initialCostEstimationModel + learnedCostEstimationModel
    cost_swap = _GenerateCostTable(costEstimationModel)

    deviceCost = PhysicalDeviceCost(deviceCostName, cost_cnot, cost_swap)
    return deviceCost