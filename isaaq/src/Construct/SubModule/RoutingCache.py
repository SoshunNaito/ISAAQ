from isaaq.src.Common.QuantumGates import *
from isaaq.src.Common.PhysicalDevice import *

from typing import Tuple

class _RoutingNode:
	def __init__(self, depth: int, back: list[int] = None, pair: Tuple[int, int] = None):
		self.depth: int = depth
		self.back: list[int] = back
		self.pair: Tuple[int, int] = pair

class RoutingCache:
	def __init__(self, graph: PhysicalDeviceGraph, maxCacheSize = 10000):
		self.graph: PhysicalDeviceGraph = graph
		self.maxCacheSize: int = maxCacheSize
		self._CreateCacheTable()

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