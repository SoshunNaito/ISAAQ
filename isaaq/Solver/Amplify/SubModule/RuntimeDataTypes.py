from dataclasses import dataclass

@dataclass
class AmplifyRuntimeSettings:
	token: str
	timeout: int
	constraint_strength: float

@dataclass
class AmplifyRuntimeInfo:
	constraint_strength: float = 0
	num_trials: int = 0
	elapsed_time: int = 0
	execution_time: int = 0
	cpu_time: int = 0
	queue_time: int = 0