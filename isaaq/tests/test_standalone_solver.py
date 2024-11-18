import os

from isaaq import StandaloneSettings, StandaloneSolver
from isaaq.Clustering import (
    ClusteringProblem,
    SolveClusteredMapping,
    SolveClusteringProblem,
)
from isaaq.Construct import ConstructCircuit
from isaaq.IO import ExportCircuit, ImportCircuit, ImportDevice
from isaaq.Scheduler import BinaryQAPScheduler


def test_standalone_solver():
    ##### device preparation #####
    originalDevice = ImportDevice("Tokyo_10", refreshCostTable=True)
    clusteringProblem = ClusteringProblem(originalDevice, numClusterDevices=2)
    clusteringResult = SolveClusteringProblem(
        clusteringProblem,
        clusterCostFunc=lambda values, weights: sum(
            [values[i] * weights[i] for i in range(len(weights))]
        )
        / sum(weights),
    )

    ##### circuit preparation #####
    inputCircuit = ImportCircuit(
        "isaaq/tests/test_input.qasm"  # OpenQASM 2.0 (containing only u() and cx()) is supported.
    )

    solver = StandaloneSolver(  # Use StandaloneSolver if you don't have a Fixstars Amplify account.
        settings=StandaloneSettings(num_iterations=20)
    )
    scheduler = BinaryQAPScheduler(solver)
    print("solver prepared")

    ##### solve mapping problem & construct circuit
    mappingResult = SolveClusteredMapping(  # Use hierarchical clustering to efficiently perform qubit routing.
        inputCircuit,
        clusteringResult,
        scheduler,
        maxLayerSize=30,
        minLayerCount=10,
        simplifyCircuit=True,
        localSearchCount=1,
    )
    outputCircuit = ConstructCircuit(
        inputCircuit,
        mappingResult,
        routingCache=None,
        addRoutingLog=True,  # ISAAQ uses routing results to update QUBO models.
    )

    output_directory = "target"
    # Create a new directory because it does not exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    output_file = output_directory + "/test_output.qasm"
    ExportCircuit(outputCircuit, output_file)

    assert os.path.exists(output_file)
