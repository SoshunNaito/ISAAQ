from collections import deque

from isaaq.src.Common.QuantumGates import *
from isaaq.src.Common.PhysicalDevice import *
from isaaq.src.Construct.SubModule.RoutingCache import *

def Routing(physicalToPhysical: list[int], graph: PhysicalDeviceGraph, cache: RoutingCache = None) -> list[CXGate]:
	ans_gates: list[CXGate] = []

	for bfs_root in range(graph.N):
		ans: list[CXGate] = []

		isFixed: list[bool] = [False] * graph.N
		placeToContent: list[int] = [p for p in physicalToPhysical]
		contentToPlace: list[int] = [0] * graph.N
		for p in range(graph.N): contentToPlace[placeToContent[p]] = p

		INF = graph.N * 100 + 1000
		distFromSrc = [INF] * graph.N
		backToSrc = [-1] * graph.N
		
		for dst in graph.rootToLeaf[bfs_root][::-1]:
			touchedNodes: list[int] = []

			src = contentToPlace[dst] # srcにある中身をdstに持っていきたい
			distToNodes: list[deque[int]] = [deque([src])]
			distFromSrc[src] = 0
			touchedNodes.append(src)

			dist_idx = 0
			while(dist_idx < len(distToNodes)):
				q = distToNodes[dist_idx]
				while(len(q) > 0):
					x = q.pop()
					if(distFromSrc[x] != dist_idx): continue
					if(x == dst):
						dist_idx = len(distToNodes)
						break

					for y in graph.neighbours[x]:
						if(isFixed[y]): continue
						v = placeToContent[y]
						d1 = graph.distanceTo[dst][y] - graph.distanceTo[dst][x] + 1
						d2 = graph.distanceTo[v][x] - graph.distanceTo[v][y] + 1
						d = distFromSrc[x] + d1 + d2
						if(d < distFromSrc[y]):
							distFromSrc[y] = d
							backToSrc[y] = x
							touchedNodes.append(y)
							while(len(distToNodes) <= d):
								distToNodes.append(deque())
							distToNodes[d].append(y)
				dist_idx += 1
			
			trace: list[int] = []
			x = dst
			while(x != -1):
				trace.append(x)
				x = backToSrc[x]
			
			for x in touchedNodes:
				distFromSrc[x] = INF
				backToSrc[x] = -1

			for i in range(len(trace) - 1)[::-1]:
				p, q = trace[i], trace[i + 1]
				a, b = placeToContent[p], placeToContent[q]
				
				# SWAP operation
				ans.append(CXGate(p, q))
				ans.append(CXGate(q, p))
				ans.append(CXGate(p, q))

				placeToContent[p], placeToContent[q] = b, a
				contentToPlace[a], contentToPlace[b] = q, p

			if(cache != None and cache.Contains(placeToContent)):
				ans.extend(cache.GetRoutingGates(placeToContent))
				break

		if(len(ans_gates) == 0 or len(ans) < len(ans_gates)):
			ans_gates = [g for g in ans]
	return ans_gates