from typing import Tuple

from isaaq.Common.QuantumGates import *
from isaaq.Common.PhysicalDevice import *

def GetParentNodes(srcList: list[int], dst: int, graph: PhysicalDeviceGraph) -> Tuple[list[int], list[int]]:
	parent: list[int] = [-1] * len(srcList)
	children: list[set[int]] = [{i} for i in range(len(srcList))]
	scoreList: list[Tuple[int, Tuple[int, int]]] = []
	for idx1 in range(len(srcList)):
		s1 = srcList[idx1]
		for idx2 in range(len(srcList)):
			s2 = srcList[idx2]
			score = max(1, 4 * (graph.distanceTo[s1][dst] - 1)) - 2 * (2 * graph.distanceTo[s1][s2] - 1)
			scoreList.append((score, (idx1, idx2)))
	scoreList.sort(reverse = True)

	for (score, (idx1, idx2)) in scoreList:
		if(idx2 in children[idx1]): continue
		if(parent[idx1] != -1): continue
		if(score <= 0): break
		parent[idx1] = idx2
		children[idx2] |= children[idx1]

	rootToLeaf: list[int] = []
	q: deque[int] = deque()
	for i in range(len(parent)):
		if(parent[i] == -1): q.append(i)
	while(len(q) > 0):
		x = q.popleft()
		rootToLeaf.append(x)
		for y in range(len(srcList)):
			if(parent[y] == x): q.append(y)
	return parent, rootToLeaf

# def GetSteinerTree_networkx(srcRoots: list[int], dst: int, graph: PhysicalDeviceGraph) -> Tuple[list[int], list[list[int]]]:
# 	G = nx.Graph()
# 	G.add_nodes_from(list(range(graph.N)))
# 	G.add_edges_from(graph.edges)
# 	tree: nx.Graph = nx.algorithms.approximation.steiner_tree(G, srcRoots + [dst])
	
# 	back: list[int] = [-1 for i in range(graph.N)]
# 	next: list[list[int]] = [[] for i in range(graph.N)]
# 	q: Deque[int] = deque()
# 	q.append(dst)
# 	while(len(q) > 0):
# 		x = q.popleft()
# 		for y in tree[x]:
# 			if(y != back[x]):
# 				q.append(y)
# 				next[x].append(y)
# 				back[y] = x

# 	return back, next

def GetSteinerTree(srcRoots: list[int], dst: int, graph: PhysicalDeviceGraph) -> Tuple[list[int], list[list[int]]]:
	hub, cost = -1, graph.N * len(srcRoots)
	for h in range(graph.N):
		c = sum([min(graph.distanceTo[src][h], graph.distanceTo[src][dst]) for src in srcRoots]) + graph.distanceTo[h][dst]
		if(c < cost): hub, cost = h, c

	back: list[int] = [-1 for i in range(graph.N)]
	next: list[list[int]] = [[] for i in range(graph.N)]
	pairs: list[Tuple[int, int]] = [(hub, dst)]
	for src in srcRoots:
		if(graph.distanceTo[src][hub] < graph.distanceTo[src][dst]): pairs.append((src, hub))
		else: pairs.append((src, dst))

	for (x, d) in pairs:
		while(True):
			if(back[x] != -1): break
			y = graph.parentTo[d][x]
			if(y == -1): break
			back[x] = y
			next[y].append(x)
			x = y
	return back, next

def _Approx_CX_line(src: int, dst: int, graph: PhysicalDeviceGraph) -> list[CXGate]:
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

def _Approx_CX_tree(x: int, next: list[list[int]], isSrc: list[bool]) -> list[CXGate]:
	if(len(next[x]) == 0): return []

	ans = []
	for y in next[x]:
		if(isSrc[y] == False): ans.append(CXGate(y, x))
		ans += _Approx_CX_tree(y, next, isSrc)
		ans.append(CXGate(y, x))
	return ans

def _RemoteCX_tree(srcList: list[int], dst: int, graph: PhysicalDeviceGraph) -> list[CXGate]:
	parent, rootToLeaf = GetParentNodes(srcList, dst, graph)
	srcRoots: list[int] = []
	isSrc: list[bool] = [False] * graph.N
	for n in rootToLeaf:
		if(parent[n] == -1):
			srcRoots.append(srcList[n])
			isSrc[srcList[n]] = True

	ans: list[CXGate] = []
	for x in rootToLeaf[::-1]:
		if(parent[x] != -1): ans += _Approx_CX_line(srcList[x], srcList[parent[x]], graph)

	back, next = GetSteinerTree(srcRoots, dst, graph)
	for x in next[dst]:
		if(isSrc[x] == False): ans.append(CXGate(x, dst))
		ans += _Approx_CX_tree(x, next, isSrc)
	for x in next[dst][::-1]:
		ans.append(CXGate(x, dst))
		ans += _Approx_CX_tree(x, next, isSrc)[::-1]
	
	for x in rootToLeaf:
		if(parent[x] != -1): ans += _Approx_CX_line(srcList[x], srcList[parent[x]], graph)

	return ans

def _RemoteCX_hub(srcList: list[int], dst: int, graph: PhysicalDeviceGraph) -> list[CXGate]:
	if(graph.N <= 50): hub_candidates = list(range(graph.N))
	else: hub_candidates = list(range(0, graph.N, graph.N // 20))

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
		ans += _Approx_CX_line(hub, dst, graph)
		for src in S1: ans += _Approx_CX_line(src, hub, graph)
		ans += _Approx_CX_line(hub, dst, graph)
	return ans

def _RemoteCX_main(srcList: list[int], dst: int, graph: PhysicalDeviceGraph) -> list[CXGate]:
	if(len(srcList) == 0): return []
	if(len(srcList) == 1): return _Exact_CX_line(srcList[0], dst, graph)

	ans_tree = _RemoteCX_tree(srcList, dst, graph)
	ans_hub = _RemoteCX_hub(srcList, dst, graph)

	if(len(ans_tree) < len(ans_hub)): return ans_tree
	else: return ans_hub

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