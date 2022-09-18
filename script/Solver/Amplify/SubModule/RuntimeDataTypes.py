class AmplifyRuntimeSettings:
	def __init__(
		self,
		token: str,
		timeout: int,
		constraint_strength: float
	):
		self.token = token
		self.timeout = timeout
		self.constraint_strength = constraint_strength

class AmplifyRuntimeInfo:
	def __init__(
		self,
		constraint_strength: float
	):
		self.constraint_strength = constraint_strength