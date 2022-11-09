from isaaq.Common.QuantumGates import *
from isaaq.Common.PhysicalDevice import *
from isaaq.Construct.SubModule.RemoteCX import *

from isaaq.Construct.SubModule.QuantumGateStack import *

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