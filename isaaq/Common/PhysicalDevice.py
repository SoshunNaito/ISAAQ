from collections import deque
from typing import Tuple

from isaaq.Common.Qubits import *

class PhysicalDeviceGraph:
	def __init__(self, name: str, N: int = 0, edges: list[Tuple[int, int]] = []):
		self.name: str = name
		self.SetGraph(N, edges)

	def SetGraph(self, N: int, edges: list[Tuple[int, int]]):
		self.N: int = N
		self.edges: list[Tuple[int, int]] = [e for e in edges]
		self.neighbours: list[set[int]] = [set() for n in range(N)]
		for edge in self.edges:
			a, b = edge
			if(a == b): continue
			self.neighbours[a].add(b)
			self.neighbours[b].add(a)
		
		# [root_node][current_node]
		self.parentTo: list[list[int]] = [[] for n in range(self.N)]
		self.distanceTo: list[list[int]] = [[] for n in range(self.N)]
		self.rootToLeaf: list[list[int]] = [[] for n in range(self.N)]
		for root in range(N): self._CalcBFSTable(root)

	def _CalcBFSTable(self, root: int):
		parents = [-1] * self.N
		distances = [self.N * 2 + 100] * self.N
		rootToLeaf: list[int] = []

		q: deque[int] = deque()
		q.append(root)
		distances[root] = 0
		while(len(q) > 0):
			x = q.popleft()
			rootToLeaf.append(x)

			d = distances[x] + 1
			for y in self.neighbours[x]:
				if(d < distances[y]):
					parents[y] = x
					distances[y] = d
					q.append(y)
		self.parentTo[root] = parents
		self.distanceTo[root] = distances
		self.rootToLeaf[root] = rootToLeaf

class PhysicalDeviceCost:
	def __init__(self, name: str, cost_cnot: list[list[float]] = [], cost_swap: list[list[float]] = []):
		self.name: str = name
		self.SetCostTable(cost_cnot, cost_swap)

	def SetCostTable(self, cost_cnot: list[list[float]], cost_swap: list[list[float]]):
		self.cost_cnot: list[list[float]] = cost_cnot
		self.cost_swap: list[list[float]] = cost_swap

class PhysicalDevice:
	def __init__(self, qubits: PhysicalQubits = None, graph: PhysicalDeviceGraph = None, cost: PhysicalDeviceCost = None):
		self.qubits: PhysicalQubits = qubits
		self.graph: PhysicalDeviceGraph = graph
		self.cost: PhysicalDeviceCost = cost

	def __str__(self):
		return "(" + self.graph.name + ", " + self.cost.name + ")"