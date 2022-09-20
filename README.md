# ISAAQ
ISAAQ is a Python package for efficient quantum circuit compilation assisted by Ising machines.

# Install
```
pip install git+https://github.com/SoshunNaito/ISAAQ.git
```

# Example
```
# prepare
circuit_in = ImportCircuit("<path_to_input_circuit>")
device = ImportDevice("<name_of_physical_device>")
problem = GenerateMappingProblem(circuit_in, device)

# solve
solver = AmplifySolver(
	settings = AmplifySettings(
		token = "<your_own_amplify_token>",
		timeout = 1000,
		max_binary_variables = 1200,
	)
)
scheduler = SequentialQAPScheduler(solver)
answer = scheduler.solve(problem)

# export
circuit_out = ConstructCircuit(circuit_in, answer)
ExportCircuit(circuit_out, "<path_to_output_circuit>")
```
