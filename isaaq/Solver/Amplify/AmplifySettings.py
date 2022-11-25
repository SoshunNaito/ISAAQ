from dataclasses import dataclass

@dataclass
class AmplifySettings:
	token: str
	timeout: int
	max_binary_variables: int = 131072
	max_num_machines: int = 1
	constraint_strength: float = 2 ** (-5)