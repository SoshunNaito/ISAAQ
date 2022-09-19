from nis import match
import os
import sys

import networkx as nx

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from isaaq.src.Common.QuantumGates import *
from isaaq.src.Common.PhysicalDevice import *

from enum import *
from isaaq.src.Construct.SubModule.RemoteCX import *

class QubitStatus(Enum):
    NONE = 0
    CONTROL = 1
    TARGET = 2

class PhysicalGateStack:
    def __init__(self, N: int):
        self.N = N

        # CXがかかっているかどうか
        self.hasCX: list[list[bool]] = [[False for j in range(N)] for i in range(N)]
        # CXの右に積み重なった1ビットゲート
        self.singleGateStack: list[list[BaseGate]] = [[] for i in range(N)]
        # 各qubitの状態
        self.qubitStatus: list[int] = [QubitStatus.NONE for i in range(N)]

    def CountCX(self, node: int, isControl: bool):
        ans = 0
        if(isControl):
            for i in range(self.N):
                if(self.hasCX[node][i]): ans += 1
        else:
            for i in range(self.N):
                if(self.hasCX[i][node]): ans += 1
        return ans

    def AddSingleGate(self, gate: Union[U3Gate, MeasureGate]):
        self.singleGateStack[gate.Qubit].append(gate)

    def AddCXGate(self, src: int, dst: int):
        if(src == dst): raise RuntimeError("srcとdstが同じです")
        if(len(self.singleGateStack[src]) > 0 or len(self.singleGateStack[dst]) > 0):
            raise RuntimeError("single gateが残っています (PopGatesを呼び出してください)")
        if(self.CountCX(src, False) > 0 or self.CountCX(dst, True) > 0):
            raise RuntimeError("非可換なCXゲートが残っています (PopGatesを呼び出してください)")

        self.hasCX[src][dst] = ~self.hasCX[src][dst]
        

    def PopGates(self, node: int, nextStatus: QubitStatus = QubitStatus.NONE) -> Tuple[list[BaseGate], list[BaseGate]]:
        CXGates: list[CXGate] = []
        singleGates: list[Union[U3Gate, MeasureGate]] = [g for g in self.singleGateStack[node]]
        self.singleGateStack[node].clear()

        if(nextStatus in [QubitStatus.NONE, QubitStatus.CONTROL]):
            for i in range(self.N):
                if(self.hasCX[i][node]):
                    CXGates.append(CXGate(i, node))
                    self.hasCX[i][node] = False

        if(nextStatus in [QubitStatus.NONE, QubitStatus.TARGET]):
            for i in range(self.N):
                if(self.hasCX[node][i]):
                    CXGates.append(CXGate(node, i))
                    self.hasCX[node][i] = False
        
        return (CXGates, singleGates)

    def PopAllGates(self) -> Tuple[list[list[BaseGate]], list[BaseGate]]:
        CXClusters: list[list[CXGate]] = []
        singleGates: list[Union[U3Gate, MeasureGate]] = []
        for node in range(self.N):
            for g in self.singleGateStack[node]: singleGates.append(g)

        CXPairs: list[Tuple[int, int]] = []
        for src in range(self.N):
            for dst in range(self.N):
                if(self.hasCX[src][dst]):
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
            vertexCover = nx.bipartite.to_vertex_cover(BG, matching)
            for v in vertexCover:
                CXCluster: list[CXGate] = []
                if(v in srcNodes):
                    for dst in range(self.N):
                        if(self.hasCX[v][dst]):
                            CXCluster.append(CXGate(v, dst))
                            self.hasCX[v][dst] = False
                else:
                    for src in range(self.N):
                        if(self.hasCX[src][v]):
                            CXCluster.append(CXGate(src, v))
                            self.hasCX[src][v] = False

                if(len(CXCluster) > 0):
                    CXClusters.append(CXCluster)
        
        return (CXClusters, singleGates)

def Placing(virtualGates: list[BaseGate], virtualToPhysical: list[int], graph: PhysicalDeviceGraph) -> list[BaseGate]:
    ans: list[BaseGate] = []
    stack = PhysicalGateStack(graph.N)

    for gate in virtualGates:
        if(isinstance(gate, U3Gate)):
            stack.AddSingleGate(
                U3Gate(
                    virtualToPhysical[gate.Qubit],
                    gate.theta, gate.phi, gate.lam
                )
            )
        elif(isinstance(gate, CXGate)):
            src, dst = virtualToPhysical[gate.Qubit_src], virtualToPhysical[gate.Qubit_dst]

            (popped_CX, popped_U3) = stack.PopGates(src, QubitStatus.CONTROL)
            for g in RemoteCX(popped_CX, graph): ans.append(g)
            for g in popped_U3: ans.append(g)

            (popped_CX, popped_U3) = stack.PopGates(dst, QubitStatus.TARGET)
            for g in RemoteCX(popped_CX, graph): ans.append(g)
            for g in popped_U3: ans.append(g)

            stack.AddCXGate(src, dst)
        elif(isinstance(gate, MeasureGate)):
            stack.AddSingleGate(
                MeasureGate(
                    virtualToPhysical[gate.Qubit],
                    gate.Cbit
                )
            )
        elif(isinstance(gate, BarrierGate)):
            # ans.append(
            #     BarrierGate(
            #         [virtualToPhysical[v] for v in gate.Qubits]
            #     )
            # )
            pass
        else:
            raise RuntimeError("Unknown gate detected: " + str(gate))

    (popped_CXList, popped_U3) = stack.PopAllGates()
    for popped_CX in popped_CXList:
        for g in RemoteCX(popped_CX, graph): ans.append(g)
    for g in popped_U3: ans.append(g)

    return ans