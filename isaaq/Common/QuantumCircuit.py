from typing import Tuple

from isaaq.Common.QuantumGates import *

class QuantumCircuit:
	def __init__(self, Qubits: list[Tuple[str, int]] = [], Cbits: list[Tuple[str, int]] = []):
		self.Qubits: list[Tuple[str, int]] = []
		self.Cbits: list[Tuple[str, int]] = []
		self.indexToQubit: list[str] = []
		self.indexToCbit: list[str] = []
		self.QubitToIndex: dict[str, int] = {}
		self.CbitToIndex: dict[str, int] = {}

		self.numQubits: int = 0
		self.numCbits: int = 0

		for Qubit in Qubits: self.AddQubits(Qubit[0], Qubit[1])
		for Cbit in Cbits: self.AddCbits(Cbit[0], Cbit[1])
		
		self.gates: list[BaseGate] = []

	def AddQubits(self, var_name: str, var_count: int):
		self.Qubits.append((var_name, var_count))
		for n in range(var_count):
			v = var_name + "[" + str(n) + "]"
			self.QubitToIndex[v] = len(self.indexToQubit)
			self.indexToQubit.append(v)
			self.numQubits = len(self.indexToQubit)
	
	def AddCbits(self, var_name: str, var_count: int):
		self.Cbits.append((var_name, var_count))
		for n in range(var_count):
			v = var_name + "[" + str(n) + "]"
			self.CbitToIndex[v] = len(self.indexToCbit)
			self.indexToCbit.append(v)
			self.numCbits = len(self.indexToCbit)

	def AddGate(self, gate: BaseGate):
		self.gates.append(gate)

	def __str__(self):
		s = ""
		s += "Qubit: " + str(self.indexToQubit) + "\n"
		s += "Cbit: " + str(self.indexToCbit) + "\n"
		s += "gates:\n"
		for g in self.gates:
			s += "\t" + str(g) + "\n"
		return s