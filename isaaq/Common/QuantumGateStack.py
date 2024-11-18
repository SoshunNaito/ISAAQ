from enum import Enum
from typing import Union, Tuple
import networkx as nx

from isaaq.Common.QuantumGates import *

class QubitStatus(Enum):
    NONE = 0
    CONTROL = 1
    TARGET = 2

class QuantumGateStack:
    def __init__(self, N: int):
        self.N = N

        # CXがかかっているかどうか
        # self.hasCX: list[list[bool]] = [[False for j in range(N)] for i in range(N)]
        self.controlToTarget: list[set[int]] = [set() for i in range(N)]
        self.targetToControl: list[set[int]] = [set() for i in range(N)]
        # CXの右に積み重なった1ビットゲート
        self.singleGateStack: list[list[BaseGate]] = [[] for i in range(N)]
        # 各qubitの状態
        self.qubitStatus: list[int] = [QubitStatus.NONE for i in range(N)]

    def CountCX(self, node: int, isControl: bool):
        ans = 0
        if(isControl):
            # for i in range(self.N):
            #     if(self.hasCX[node][i]): ans += 1
            ans = len(self.controlToTarget[node])
        else:
            # for i in range(self.N):
            #     if(self.hasCX[i][node]): ans += 1
            ans = len(self.targetToControl[node])
        return ans

    def AddSingleGate(self, gate: Union[U3Gate, MeasureGate]):
        self.singleGateStack[gate.Qubit].append(gate)

    def AddCXGate(self, src: int, dst: int):
        if(src == dst): raise RuntimeError("srcとdstが同じです")
        if(len(self.singleGateStack[src]) > 0 or len(self.singleGateStack[dst]) > 0):
            raise RuntimeError("single gateが残っています (PopGatesを呼び出してください)")
        if(self.CountCX(src, False) > 0 or self.CountCX(dst, True) > 0):
            raise RuntimeError("非可換なCXゲートが残っています (PopGatesを呼び出してください)")

        # self.hasCX[src][dst] = ~self.hasCX[src][dst]
        if dst in self.controlToTarget[src]:
            self.controlToTarget[src].remove(dst)
            self.targetToControl[dst].remove(src)
        else:
            self.controlToTarget[src].add(dst)
            self.targetToControl[dst].add(src)

    def PopGates(self, node: int, nextStatus: QubitStatus) -> Tuple[list[BaseGate], list[BaseGate]]:
        CXGates: list[CXGate] = []
        singleGates: list[Union[U3Gate, MeasureGate]] = [g for g in self.singleGateStack[node]]
        self.singleGateStack[node].clear()

        if(len(singleGates) > 0 or nextStatus == QubitStatus.CONTROL):
            n = node
            # for i in range(self.N):
            #     if(self.hasCX[i][node]):
            #         CXGates.append(CXGate(i, node))
            #         self.hasCX[i][node] = False
            #         n = i
            for ctrl in self.targetToControl[node]:
                CXGates.append(CXGate(ctrl, node))
                self.controlToTarget[ctrl].remove(node)
                n = ctrl
            self.targetToControl[node].clear()
            
            if(len(CXGates) == 1):
                # for i in range(self.N):
                #     if(self.hasCX[n][i]):
                #         CXGates.append(CXGate(n, i))
                #         self.hasCX[n][i] = False
                for tgt in self.controlToTarget[n]:
                    CXGates.append(CXGate(n, tgt))
                    self.targetToControl[tgt].remove(n)
                self.controlToTarget[n].clear()

        if(len(singleGates) > 0 or nextStatus == QubitStatus.TARGET):
            n = node
            # for i in range(self.N):
            #     if(self.hasCX[node][i]):
            #         CXGates.append(CXGate(node, i))
            #         self.hasCX[node][i] = False
            #         n = i
            for tgt in self.controlToTarget[node]:
                CXGates.append(CXGate(node, tgt))
                self.targetToControl[tgt].remove(node)
                n = tgt
            self.controlToTarget[node].clear()
            
            if(len(CXGates) == 1):
                # for i in range(self.N):
                #     if(self.hasCX[i][n]):
                #         CXGates.append(CXGate(i, n))
                #         self.hasCX[i][n] = False
                for ctrl in self.targetToControl[n]:
                    CXGates.append(CXGate(ctrl, n))
                    self.controlToTarget[ctrl].remove(n)
                self.targetToControl[n].clear()
        
        return (CXGates, singleGates)

    def PopAllGates(self) -> Tuple[list[list[BaseGate]], list[BaseGate]]:
        CXClusters: list[list[CXGate]] = []
        singleGates: list[Union[U3Gate, MeasureGate]] = []
        for node in range(self.N):
            for g in self.singleGateStack[node]: singleGates.append(g)

        CXPairs: list[Tuple[int, int]] = []
        for src in range(self.N):
            # for dst in range(self.N):
            #     if(self.hasCX[src][dst]):
            #         CXPairs.append((src, dst))
            for dst in self.controlToTarget[src]:
                CXPairs.append((src, dst))

        if(len(CXPairs) > 0):
            srcNodes = list(set([p[0] for p in CXPairs]))
            dstNodes = list(set([p[1] for p in CXPairs]))
            BG = nx.Graph()

            BG.add_nodes_from(srcNodes, bipartite = 0)
            BG.add_nodes_from(dstNodes, bipartite = 1)
            BG.add_edges_from(CXPairs)
            BG.add_edges_from([(srcNodes[0], p[1]) for p in CXPairs]) # 無理やり連結にする

            matching = nx.bipartite.maximum_matching(BG)
            vertexCover: list[int] = nx.bipartite.to_vertex_cover(BG, matching)
            for v in vertexCover:
                CXCluster: list[CXGate] = []
                if(v in srcNodes):
                    # for dst in range(self.N):
                    #     if(self.hasCX[v][dst]):
                    #         CXCluster.append(CXGate(v, dst))
                    #         self.hasCX[v][dst] = False
                    for dst in self.controlToTarget[v]:
                        CXCluster.append(CXGate(v, dst))
                        self.targetToControl[dst].remove(v)
                    self.controlToTarget[v].clear()
                else:
                    # for src in range(self.N):
                    #     if(self.hasCX[src][v]):
                    #         CXCluster.append(CXGate(src, v))
                    #         self.hasCX[src][v] = False
                    for src in self.targetToControl[v]:
                        CXCluster.append(CXGate(src, v))
                        self.controlToTarget[src].remove(v)
                    self.targetToControl[v].clear()

                if(len(CXCluster) > 0):
                    CXClusters.append(CXCluster)
        
        return (CXClusters, singleGates)