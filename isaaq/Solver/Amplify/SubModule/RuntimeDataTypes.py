from dataclasses import dataclass

@dataclass
class AmplifyRuntimeSettings:
	token: str = ""
	timeout: int = 1000
	constraint_strength: float = 1.0
	timeout_total: float = None

@dataclass
class AmplifyRuntimeInfo:
	success: bool = True
	constraint_strength: float = 0
	num_trials: int = 0
	elapsed_time: int = 0
	execution_time: int = 0
	cpu_time: int = 0
	queue_time: int = 0