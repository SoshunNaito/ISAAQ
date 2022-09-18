class BaseGate:
	def __str__(self):
		return "BaseGate"

	def read(self, gate_str: str):
		pass

	def write(self) -> str:
		return "BaseGate"

class BarrierGate(BaseGate):
	def __init__(self, Qubits_param: list[int] = []):
		self.set(Qubits_param)

	def set(self, Qubits_param: list[int]):
		self.Qubits: list[int] = [q for q in Qubits_param]

	def __str__(self):
		return "BarrierGate: " + (",".join(["Q" + str(idx) for idx in self.Qubits]))

	def read(self, gate_str: str):
		if(len(gate_str) < 7 or gate_str[:7] != "barrier"): return
		gate_str = gate_str[7:].replace(";", "").strip()
		vars = gate_str.split(",")
		self.set([int(v[1:]) for v in vars])

	def write(self) -> str:
		return "barrier " + ",".join(["Q" + str(idx) for idx in self.Qubits]) + ";"
		

class MeasureGate(BaseGate):
	def __init__(self, Qubit_param: int = 0, Cbit_param: int = 0):
		self.set(Qubit_param, Cbit_param)

	def set(self, Qubit_param: int, Cbit_param: int):
		self.Qubit: int = Qubit_param
		self.Cbit: int = Cbit_param

	def __str__(self):
		return "MeasureGate: Q" + str(self.Qubit) + " -> C" + str(self.Cbit)

	def read(self, gate_str: str):
		if(len(gate_str) < 7 or gate_str[:7] != "measure"): return
		gate_str = gate_str[7:].replace(";", "").strip()
		vars = gate_str.split()
		self.set(int(vars[0][1:]), int(vars[2][1:]))

	def write(self) -> str:
		return "measure Q" + str(self.Qubit) + " -> C" + str(self.Cbit) + ";"

class U3Gate(BaseGate):
	def __init__(self, Qubit_param: int = 0, theta_param: str = "0", phi_param: str = "0", lam_param: str = "0"):
		self.set(Qubit_param, theta_param, phi_param, lam_param)

	def set(self, Qubit_param: int, theta_param: str, phi_param: str, lam_param: str):
		self.Qubit: int = Qubit_param
		self.theta: str = theta_param
		self.phi: str = phi_param
		self.lam: str = lam_param

	def __str__(self):
		return "U3Gate: Q" + str(self.Qubit) + " (" + self.theta + "," + self.phi + "," + self.lam + ")"

	def read(self, gate_str: str):
		if(len(gate_str) < 1 or gate_str[:1] != "u"): return
		gate_str = gate_str[gate_str.find("("):].replace(";", "").strip()
		gate_str = gate_str.replace("(", "").replace(")", "").replace(",", " ")
		vars = gate_str.split()
		self.set(int(vars[3][1:]), vars[0], vars[1], vars[2])

	def write(self) -> str:
		return "u(" + self.theta + "," + self.phi + "," + self.lam +  ") Q" + str(self.Qubit) + ";"

class CXGate(BaseGate):
	def __init__(self, Qubit_src_param: int = 0, Qubit_dst_param: int = 0):
		self.set(Qubit_src_param, Qubit_dst_param)

	def set(self, Qubit_src_param: int, Qubit_dst_param: int):
		self.Qubit_src: int = Qubit_src_param
		self.Qubit_dst: int = Qubit_dst_param

	def __str__(self):
		return "CXGate: Q" + str(self.Qubit_src) + " -> Q" + str(self.Qubit_dst)

	def read(self, gate_str: str):
		if(len(gate_str) < 2 or gate_str[:2] != "cx"): return
		gate_str = gate_str[2:].replace(";", "").strip()
		vars = gate_str.replace(",", " ").split()
		self.set(int(vars[0][1:]), int(vars[1][1:]))

	def write(self) -> str:
		return "cx Q" + str(self.Qubit_src) + ",Q" + str(self.Qubit_dst) + ";"