class AmplifySettings:
	def __init__(
		self, token: str, timeout: int,
		max_binary_variables: int = 131072,
		max_num_machines: int = 1,
		constraint_strength: float = 2 ** (-5)
	):
		self.token = token
		self.timeout = timeout
		self.max_binary_variables = max_binary_variables
		self.max_num_machines = max_num_machines
		self.constraint_strength = constraint_strength