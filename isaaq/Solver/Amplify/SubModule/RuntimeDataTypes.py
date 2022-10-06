from dataclasses import dataclass

@dataclass
class AmplifyRuntimeSettings:
	token: str
	timeout: int
	constraint_strength: float

@dataclass
class AmplifyRuntimeInfo:
	constraint_strength: float