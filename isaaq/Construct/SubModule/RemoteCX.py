from typing import Tuple

from isaaq.Common.QuantumGates import *
from isaaq.Common.PhysicalDevice import *

def _Approx_CX_line(src: int, dst: int, graph: PhysicalDeviceGraph) -> list[CXGate]:
	if(graph.distanceTo[src][dst] == 1): return [CXGate(src, dst)]
	ans = []
	x = dst
	while(True):
		y = graph.parentTo[src][x]
		if(y == -1): break
		ans.append(CXGate(y, x))
		x = y
	return ans + ans[:-1][::-1]

def _Exact_CX_line(src: int, dst: int, graph: PhysicalDeviceGraph) -> list[CXGate]:
	if(graph.distanceTo[src][dst] == 1): return [CXGate(src, dst)]
	return _Approx_CX_line(src, dst, graph) + _Approx_CX_line(src, graph.parentTo[src][dst], graph)

def _RemoteCX_tree(srcList: list[int], dst: int, graph: PhysicalDeviceGraph) -> list[CXGate]:
	allList = [dst] + srcList
	edges: list[Tuple[int, int, int]] = []
	for i in range(len(allList)):
		for j in range(i + 1, len(allList)):
			if(i == 0): d = max(1, 4 * (graph.distanceTo[allList[i]][allList[j]] - 1))
			else: d = 2 * (2 * graph.distanceTo[allList[i]][allList[j]] - 1)
			edges.append((d, i, j))

	# create spanning tree
	next: list[list[int]] = [[] for _ in allList]
	back: list[int] = [-1 for _ in allList]

	parent: list[int] = [i for i in range(len(allList))]
	for (d, _i, _j) in sorted(edges):
		i, j = _i, _j
		while(parent[i] != i): i, parent[i] = parent[i], parent[parent[i]]
		while(parent[j] != j): j, parent[j] = parent[j], parent[parent[j]]
		if(i == j): continue

		next[_i].append(_j)
		next[_j].append(_i)
		parent[i] = j

	bfsOrder: list[int] = [0]
	for i in range(len(allList)):
		for j in next[i]:
			bfsOrder.append(j)
			back[j] = i
			next[j].remove(i)
	
	# circuit construction
	ans: list[CXGate] = []
	for i in bfsOrder[::-1]:
		if(i != 0 and back[i] != 0):
			ans += _Approx_CX_line(allList[i], allList[back[i]], graph)
	
	for i in next[0]: ans += _Exact_CX_line(allList[i], dst, graph)
	
	for i in bfsOrder:
		if(i != 0 and back[i] != 0):
			ans += _Approx_CX_line(allList[i], allList[back[i]], graph)
	
	return ans	

def _RemoteCX_hub(srcList: list[int], dst: int, graph: PhysicalDeviceGraph) -> list[CXGate]:
	if(graph.N <= 50): hub_candidates = list(range(graph.N))
	else: hub_candidates = list(range(0, graph.N, graph.N // 20))

	# choose the best position
	hub, cost = -1, graph.N * len(srcList) * 1000
	for h in hub_candidates:
		c = 0
		if(h == dst):
			for src in srcList:
				c += max(1, 4 * (graph.distanceTo[src][dst] - 1))
		elif h in srcList:
			for src in srcList:
				if(src == h):
					c += max(1, 4 * (graph.distanceTo[src][dst] - 1))
				else:
					c0 = max(1, 4 * (graph.distanceTo[src][dst] - 1))
					c1 = 2 * max(1, 2 * graph.distanceTo[src][h] - 1)
					c += min(c0, c1)
		else:
			c += 2 * max(1, 2 * graph.distanceTo[h][dst] - 1)
			for src in srcList:
				c0 = max(1, 4 * (graph.distanceTo[src][dst] - 1))
				c1 = 2 * max(1, 2 * graph.distanceTo[src][h] - 1)
				c += min(c0, c1)
		if(c < cost):
			hub = h
			cost = c
	
	# circuit construction
	ans: list[CXGate] = []
	if(hub == dst):
		for src in srcList: ans += _Exact_CX_line(src, dst, graph)
	elif hub in srcList:
		S0, S1 = [hub], []
		for src in srcList:
			if(src == hub): continue
			c0 = max(1, 4 * (graph.distanceTo[src][dst] - 1))
			c1 = 2 * max(1, 2 * graph.distanceTo[src][hub] - 1)
			if(c0 < c1): S0.append(src)
			else: S1.append(src)

		for src in S1: ans += _Approx_CX_line(src, hub, graph)
		for src in S0: ans += _Exact_CX_line(src, dst, graph)
		for src in S1: ans += _Approx_CX_line(src, hub, graph)
	else:
		S0, S1 = [], []
		for src in srcList:
			c0 = max(1, 4 * (graph.distanceTo[src][dst] - 1))
			c1 = 2 * max(1, 2 * graph.distanceTo[src][hub] - 1)
			if(c0 < c1): S0.append(src)
			else: S1.append(src)

		for src in S0: ans += _Exact_CX_line(src, dst, graph)

		for src in S1: ans += _Approx_CX_line(src, hub, graph)
		ans += [CXGate(gate.Qubit_dst, gate.Qubit_src) for gate in _Approx_CX_line(dst, hub, graph)]
		for src in S1: ans += _Approx_CX_line(src, hub, graph)
		ans += [CXGate(gate.Qubit_dst, gate.Qubit_src) for gate in _Approx_CX_line(dst, hub, graph)]

	if(len(ans) != cost):
		raise RuntimeError("len(ans) != cost")
	return ans

def _RemoteCX_main(srcList: list[int], dst: int, graph: PhysicalDeviceGraph) -> list[CXGate]:
	if(len(srcList) == 0): return []
	if(len(srcList) == 1): return _Exact_CX_line(srcList[0], dst, graph)

	# ans_tree = _RemoteCX_tree(srcList, dst, graph)
	ans_hub = _RemoteCX_hub(srcList, dst, graph)

	# if(len(ans_tree) != len(ans_hub)): print(str(len(ans_hub)) + " vs " + str(len(ans_tree)))

	# if(len(ans_tree) < len(ans_hub)): return ans_tree
	# else: return ans_hub
	return ans_hub

def RemoteCX(CXGates: list[CXGate], graph: PhysicalDeviceGraph) -> list[CXGate]:
	srcQubits, dstQubits = set(), set()
	for gate in CXGates:
		srcQubits.add(gate.Qubit_src)
		dstQubits.add(gate.Qubit_dst)
	
	if(len(dstQubits) == 1):
		return _RemoteCX_main(list(srcQubits), list(dstQubits)[0], graph)
	elif(len(srcQubits) == 1):
		gates = _RemoteCX_main(list(dstQubits), list(srcQubits)[0], graph)
		return [CXGate(gate.Qubit_dst, gate.Qubit_src) for gate in gates]
	else:
		return []

# def RemoteCX(CXGates: list[CXGate], graph: PhysicalDeviceGraph) -> list[CXGate]:
# 	ans: list[CXGate] = []
# 	for gate in CXGates:
# 		src, dst = gate.Qubit_src, gate.Qubit_dst
		
# 		q = src
# 		Q: list[int] = []
# 		while(q != -1):
# 			Q.append(q)
# 			q = graph.parentTo[dst][q]
		
# 		if(len(Q) <= 1):
# 			raise RuntimeError("RemoteCXの長さが正しくありません")
# 		if(len(Q) == 2):
# 			ans.append(CXGate(Q[0], Q[1]))
# 		else:
# 			for i in range(1, len(Q) - 1)[::-1]:
# 				ans.append(CXGate(Q[i], Q[i + 1]))
# 			for i in range(len(Q) - 2):
# 				ans.append(CXGate(Q[i], Q[i + 1]))
# 			for i in range(1, len(Q) - 1)[::-1]:
# 				ans.append(CXGate(Q[i], Q[i + 1]))
# 			for i in range(len(Q) - 2):
# 				ans.append(CXGate(Q[i], Q[i + 1]))
# 	return ans