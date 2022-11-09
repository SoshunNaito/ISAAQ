from collections import deque

from isaaq.Common.QuantumGates import *
from isaaq.Common.PhysicalDevice import *
from isaaq.Construct.SubModule.RoutingCache import *

import random

def Routing(physicalToPhysical: list[int], graph: PhysicalDeviceGraph, cache: RoutingCache = None, rootMaxCount: int = 0) -> list[CXGate]:
	ans_gates: list[CXGate] = []

	if(rootMaxCount <= 0 or graph.N <= rootMaxCount):
		rootToLeafTable = [graph.rootToLeaf[i] for i in range(graph.N)]
	else:
		rootToLeafTable = [
			graph.rootToLeaf[i]
			for i in random.sample(list(range(graph.N)), min(rootMaxCount, graph.N))
		]
	diffListTable = [None] * len(rootToLeafTable)

	for i in range(cache.rootToLeafTableSize):
		rootToLeafTable.append(cache.rootToLeafTable[i])
		diffListTable.append(cache.diffListTable[i])

	# for bfs_root in bfs_roots:
	for root_idx in range(len(rootToLeafTable)):
		rootToLeaf = rootToLeafTable[root_idx]
		diffList = diffListTable[root_idx]
		
		ans: list[CXGate] = []

		isFixed: list[bool] = [False] * graph.N
		placeToContent: list[int] = [p for p in physicalToPhysical]
		contentToPlace: list[int] = [-1] * graph.N
		for p in range(graph.N):
			if(placeToContent[p] != -1):
				contentToPlace[placeToContent[p]] = p

		INF = graph.N * 100 + 1000
		distFromSrc = [INF] * graph.N
		backToSrc = [-1] * graph.N

		# 部分グラフ上の最短経路情報
		distanceTo: list[list[int]] = [[graph.distanceTo[src][x] for x in range(graph.N)] for src in range(graph.N)]
		
		for dst_idx in range(graph.N)[::-1]:
			if(cache != None and cache.Contains(placeToContent)):
				ans.extend(cache.GetRoutingGates(placeToContent))
				break
			
			dst = rootToLeaf[dst_idx]
			touchedNodes: list[int] = []

			src = contentToPlace[dst] # srcにある中身をdstに持っていきたい
			if(src != -1):
				distToNodes: list[deque[int]] = [deque([src])]
				distFromSrc[src] = 0
				touchedNodes.append(src)

				dist = 0
				while(dist < len(distToNodes)):
					q = distToNodes[dist]
					while(len(q) > 0):
						x = q.pop()
						if(distFromSrc[x] != dist): continue
						if(x == dst):
							dist = len(distToNodes)
							isFixed[dst] = True
							break

						for y in graph.neighbours[x]:
							if(isFixed[y]): continue
							v = placeToContent[y]
							d1 = distanceTo[dst][y] - distanceTo[dst][x] + 1
							if(v == -1): d2 = 1
							else: d2 = distanceTo[v][x] - distanceTo[v][y] + 1
							d = distFromSrc[x] + d1 + d2
							if(d < distFromSrc[y]):
								distFromSrc[y] = d
								backToSrc[y] = x
								touchedNodes.append(y)
								while(len(distToNodes) <= d):
									distToNodes.append(deque())
								distToNodes[d].append(y)
					dist += 1
				
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

			if(diffList != None):
				tableDiff = diffList[dst_idx]
				for (src, node, old_val, new_val) in tableDiff:
					if(distanceTo[src][node] != new_val):
						raise RuntimeError("invalid diffList: " + str(distanceTo[src][node]) + " != " + str(new_val))
					distanceTo[src][node] = old_val

		if(len(ans_gates) == 0 or len(ans) < len(ans_gates)):
			ans_gates = [g for g in ans]
	return ans_gates