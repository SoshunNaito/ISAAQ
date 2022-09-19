import os
import sys

from isaaq.src.Common.QubitMapping import *
from .PhysicalDevice import *

def ExportMappingResult(mapping: QubitMapping, filepath: str):
	S = []
	S.append(str(mapping.numLayers) + "\n")
	for layer in mapping.layers:
		S.append(" ".join([str(s) for s in layer.virtualToPhysical]) + "\n")
	with open(filepath, "w") as f:
		f.writelines(S)

def ImportMappingResult(dst_mapping: QubitMapping, filepath: str):
	with open(filepath, "r") as f:
		S = f.readlines()
	numLayers = int(S[0].strip())

	S = S[1:]
	for n in range(numLayers):
		dst_mapping.layers[n].virtualToPhysical = []
		A = S[n].strip().split()
		A = [int(a) for a in A]
		if(len(A) != dst_mapping.layers[n].virtualQubits.N):
			raise RuntimeError("mapping結果の長さ(仮想Qubit数)が異なります")
		for a in A:
			if(a < 0 or a >= dst_mapping.physicalDevice.qubits.N):
				raise RuntimeError("mapping結果(物理Qubit番号)が正しくありません")
			dst_mapping.layers[n].virtualToPhysical.append(a)