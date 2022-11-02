from isaaq.Common.QuantumGates import *
from isaaq.Common.PhysicalDevice import *
from typing import Tuple

import random

class _RoutingNode:
	def __init__(self, depth: int, back: list[int] = None, pair: Tuple[int, int] = None):
		self.depth = depth
		self.back = back
		self.pair = pair

class RoutingCache:
	def __init__(self, graph: PhysicalDeviceGraph, maxCacheSize: int = -1, rootToLeafTableSize: int = 0):
		if(maxCacheSize == -1): maxCacheSize = 1000000 // graph.N

		self.graph: PhysicalDeviceGraph = graph
		self.maxCacheSize: int = maxCacheSize
		self.rootToLeafTableSize: int = rootToLeafTableSize
		self._CreateCacheTable()
		self._CreateRootToLeafTable()

	def _CreateCacheTable(self):
		self.cacheTable: dict[list[int], _RoutingNode] = {}
		root = list(range(self.graph.N))
		self.cacheTable[str(root)] = _RoutingNode(0, None, None)

		q: deque[list[int]] = deque()
		q.append(root)
		while(len(q) > 0 and len(self.cacheTable) < self.maxCacheSize):
			X = q.popleft()
			depth = self.cacheTable[str(X)].depth
			for (u, v) in self.graph.edges:
				Y = [x for x in X]
				Y[u], Y[v] = Y[v], Y[u]
				if(str(Y) in self.cacheTable.keys() and self.cacheTable[str(Y)].depth <= depth + 3):
					continue
				q.append(Y)
				self.cacheTable[str(Y)] = _RoutingNode(depth + 3, X, (u, v))

	def _CreateRootToLeafTable(self):
		self.rootToLeafTable: list[list[int]] = []
		for t in range(self.rootToLeafTableSize):
			bfsOrder: list[int] = [-1 for i in range(self.graph.N)]
			weights: list[int] = [0 for i in range(self.graph.N)]
			
			for i in range(self.graph.N):
				if(i == 0):
					x = random.randrange(self.graph.N)
				else:
					x = random.choices(list(range(self.graph.N)), weights = weights, k = 1)[0]
				bfsOrder[x] = i
				weights[x] = 0

				for y in self.graph.neighbours[x]:
					if(bfsOrder[y] == -1): weights[y] += 1

			rootToLeaf: list[int] = [-1 for i in range(self.graph.N)]
			for i in range(self.graph.N): rootToLeaf[bfsOrder[i]] = i

			self.rootToLeafTable.append(rootToLeaf)
	
	def Contains(self, placeToContent: list[int]) -> bool:
		return (str(placeToContent) in self.cacheTable.keys())

	def GetRoutingGates(self, placeToContent: list[int]) -> list[CXGate]:
		if(str(placeToContent) not in self.cacheTable.keys()):
			raise RuntimeError("placeToContent not found in cache")
		ans = []
		while(self.cacheTable[str(placeToContent)].back != None):
			p, q = self.cacheTable[str(placeToContent)].pair

			# SWAP operation
			ans.append(CXGate(p, q))
			ans.append(CXGate(q, p))
			ans.append(CXGate(p, q))

			placeToContent = self.cacheTable[str(placeToContent)].back
		return ans