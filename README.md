# ISAAQ
ISAAQ is a Python package for efficient quantum circuit compilation assisted by Ising machines.

# Install
```
pip install git+https://github.com/SoshunNaito/ISAAQ.git
```

# Example
```
from isaaq.IO import *
from isaaq.Clustering import *
from isaaq.Scheduler import *
from isaaq.Solver import AmplifySolver, AmplifySettings
from isaaq.Construct import ConstructCircuit

##### device preparation #####
originalDevice = ImportDevice("<name_of_device>", refreshCostTable = True)
clusteringProblem = ClusteringProblem(originalDevice, numClusterDevices = 5)
clusteringResult = SolveClusteringProblem(
    clusteringProblem,
    clusterCostFunc = lambda values, weights:
        sum([values[i] * weights[i] for i in range(len(weights))]) / sum(weights)
)
print("device prepared")


##### circuit preparation #####
inputCircuit = ImportCircuit("<path_to_inputCircuit>") # OpenQASM 2.0 files are available.
print("circuit prepared")


##### solver preparation #####
solver = AmplifySolver(
	settings = AmplifySettings(
		token = "********************************",
		timeout = 1000,
		max_binary_variables = 2000,
		max_num_machines = 1,
        constraint_strength = 2.0
	)
)
# solver = StandaloneSolver( # Use StandaloneSolver in case you don't have a Fixstars Amplify account.
# 	settings = StandaloneSettings(
# 		num_iterations=20
# 	)
# )
scheduler = BinaryQAPScheduler(solver)
print("solver prepared")


##### solve mapping problem & construct circuit
mappingResult = SolveClusteredMapping( # Use hierarchical clustering to efficiently perform qubit routing.
    inputCircuit, clusteringResult, scheduler,
    maxLayerSize = 30,
    minLayerCount = 10,
    simplifyCircuit = True,
    useLocalSearch = True
)
# mappingResult = solver.solve( # You can use solver.solve() directly when the physical device is small enough.
# 	GenerateMappingProblem(
# 		circuit = inputCircuit,
# 		device = originalDevice,
# 		maxLayerSize = 30,
# 		minLayerCount = 10,
# 		simplifyCircuit = True
# 	)
# )
outputCircuit = ConstructCircuit(
    inputCircuit, mappingResult,
    routingCache = None,
    addRoutingLog = True # ISAAQ uses routing results to update QUBO models.
)

ExportCircuit(outputCircuit, "<path_to_export_outputCircuit>")
```
