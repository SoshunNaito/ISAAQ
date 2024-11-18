from isaaq.Clustering import ClusteringResult
from isaaq.Common import QuantumCircuit, QubitMapping, QubitMappingProblem
from isaaq.Problem import GenerateMappingProblem
from isaaq.Scheduler import BaseQAPScheduler


def SolveClusteredMapping(
    inputCircuit: QuantumCircuit,
    clusteringResult: ClusteringResult,
    QAPScheduler: BaseQAPScheduler,
    maxLayerSize: int = -1,
    minLayerCount: int = 1,
    simplifyCircuit: bool = False,
    localSearchCount: int = 0,
) -> QubitMapping:

    mappingProblem: QubitMappingProblem = None
    mappingResult: QubitMapping = None
    for i in range(clusteringResult.numClusterDevices):
        if i == 0:
            mappingProblem = GenerateMappingProblem(
                inputCircuit,
                clusteringResult.clusterDevices[0],
                maxLayerSize,
                minLayerCount,
                simplifyCircuit,
            )
            mappingResult = QAPScheduler.solve(mappingProblem)
        else:
            mappingProblem = QubitMappingProblem(
                clusteringResult.clusterDevices[i],
                mappingProblem.layers,
                [
                    [
                        [
                            n
                            for n in clusteringResult.clusterMappings[i][
                                layer.virtualToPhysical[v]
                            ]
                        ]
                        for v in range(inputCircuit.numQubits)
                    ]
                    for layer in mappingResult.layers
                ],
            )
            mappingResult = QAPScheduler.solve(mappingProblem)

        for _count in range(localSearchCount):
            graph = clusteringResult.clusterDevices[i].graph
            mappingProblem = QubitMappingProblem(
                clusteringResult.clusterDevices[i],
                mappingProblem.layers,
                [
                    [
                        list(
                            graph.neighbours[layer.virtualToPhysical[v]]
                            | {layer.virtualToPhysical[v]}
                        )
                        for v in range(inputCircuit.numQubits)
                    ]
                    for layer in mappingResult.layers
                ],
            )
            mappingResult = QAPScheduler.solve(mappingProblem)

    return mappingResult
