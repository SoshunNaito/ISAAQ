import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from Common.QuantumCircuit import *
from Common.QuantumGates import *

import re

def ReadGate(s: str) -> BaseGate:
	if(s[:7] == "barrier"):
		gate = BarrierGate()
		gate.read(s)
	elif(s[:7] == "measure"):
		gate = MeasureGate()
		gate.read(s)
	elif(s[:1] == "u"):
		gate = U3Gate()
		gate.read(s)
	elif(s[:2] == "cx"):
		gate = CXGate()
		gate.read(s)
	else:
		raise RuntimeError("ゲート読み込みに失敗しました : " + s)
	return gate

def ImportCircuit(filepath: str) -> QuantumCircuit:
	QC = QuantumCircuit()
	with open(filepath, mode = "r") as f:
		S = f.readlines()

	##########   detect variables   ##########

	for s in S:
		A = s.split()
		if(A[0] == "qreg"):
			i,j = A[1].find("["), A[1].find("]")
			var_name = A[1][:i]
			var_count = int(A[1][i+1:j])
			QC.AddQubits(var_name, var_count)

		if(A[0] == "creg"):
			i,j = A[1].find("["), A[1].find("]")
			var_name = A[1][:i]
			var_count = int(A[1][i+1:j])
			QC.AddCbits(var_name, var_count)

	##########   detect gates   ##########

	for s in S:
		s0 = s
		try:
			if(s[:4] == "qreg" or s[:4] == "creg" or s[:8] == "OPENQASM" or s[:7] == "include"): continue
			s = s.replace(";","").replace("u3(","u(")

			for (name, _) in QC.Qubits:
				vars = re.findall(name + "\[[0-9]+\]", s)
				for v in vars:
					s = s.replace(v, "Q" + str(QC.QubitToIndex[v]))
			for (name, _) in QC.Cbits:
				vars = re.findall(name + "\[[0-9]+\]", s)
				for v in vars:
					s = s.replace(v, "C" + str(QC.CbitToIndex[v]))

			QC.AddGate(ReadGate(s))
		except:
			raise RuntimeError("Error detected: " + s0)
	
	return QC

def ExportCircuit(QC: QuantumCircuit, filepath: str):
	S = []
	S.append("OPENQASM 2.0;\n")
	S.append('include "qelib1.inc";\n')
	for (Qubit_name, Qubit_count) in QC.Qubits:
		if(Qubit_count == 0): continue
		S.append("qreg " + Qubit_name + "[" + str(Qubit_count) + "];\n")
	for (Cbit_name, Cbit_count) in QC.Cbits:
		if(Cbit_count == 0): continue
		S.append("creg " + Cbit_name + "[" + str(Cbit_count) + "];\n")
	
	for gate in QC.gates:
		out_str = ""
		buf = ""
		for c in gate.write():
			if(buf != ""):
				if(c.isdecimal()): buf += c
				else:
					if(buf[0] == "Q"): out_str += QC.indexToQubit[int(buf[1:])]
					else: out_str += QC.indexToCbit[int(buf[1:])]
					buf = ""
					
					if(c == "Q" or c == "C"): buf = c
					else: out_str += c
			elif(c == "Q" or c == "C"): buf = c
			else: out_str += c
		if(buf != ""):
			if(buf[0] == "Q"): out_str += QC.indexToQubit[int(buf[1:])]
			else: out_str += QC.indexToCbit[int(buf[1:])]
			buf = ""
		S.append(out_str + "\n")
	
	with open(filepath, mode = "w") as f:
		f.writelines(S)