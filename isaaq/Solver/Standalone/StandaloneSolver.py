from isaaq.Common.QubitMapping import *
from isaaq.Common.QubitMappingProblem import *
from isaaq.Solver.BaseQAPSolver import *
from isaaq.IO.QubitMappingProblem import *
from isaaq.IO.QubitMappingResult import *

from isaaq.Scheduler.QAPSchedulers import *

from ortools.graph.python import max_flow, min_cost_flow
import numpy as np

from dataclasses import dataclass

@dataclass
class StandaloneSettings:
	num_iterations: int = 20

class StandaloneSolver(BaseQAPSolver):
	def __init__(self, settings: StandaloneSettings):
		super().__init__()
		self.settings = settings

	def _eval_cost(self, arr: list[int], potential: list[float], interation: list[list[float]]) -> float:
		val = 0
		for a in arr:
			val += potential[a]
			for b in arr:
				val += interation[a][b]
		return val

	def _find_mapping(
		self,
		virtualQubits: VirtualQubits, physicalQubits: PhysicalQubits,
		candidates: list[list[int]],
		potential: list[float], interaction: list[list[float]],
		distances: list[list[int]]
	) -> list[int]:

		virtualToPhysical = None
		virtualToPhysical_ans, val_ans = None, 0
		for itr in range(self.settings.num_iterations):
			source, sink = 0, virtualQubits.N + physicalQubits.N + 1
			v_list = [n + 1 for n in range(virtualQubits.N)]
			p_list = [n + virtualQubits.N + 1 for n in range(physicalQubits.N)]

			edges: list[Tuple[int, int, int, float]] = []

			# source -> virtual qubits
			for v_idx in range(virtualQubits.N):
				vq = v_list[v_idx]
				edges.append((source, vq, 1, 0))

			# virtual qubits -> physical qubits
			e_idx = 0
			for v_idx in range(virtualQubits.N):
				vq = v_list[v_idx]
				for p_idx in candidates[v_idx]:
					pq = p_list[p_idx]

					cost = potential[e_idx]
					if(virtualToPhysical != None):
						e_idx2 = 0
						for v_idx2 in range(virtualQubits.N):
							for p_idx2 in candidates[v_idx2]:
								if(virtualToPhysical[v_idx2] == p_idx2):
									cost += interaction[e_idx][e_idx2]
								e_idx2 += 1

						if(pq != virtualToPhysical[v_idx]):
							cost += distances[p_idx][virtualToPhysical[v_idx]] * itr / self.settings.num_iterations * 5

					edges.append((vq, pq, 1, cost))
					e_idx += 1
			
			# physical qubits -> sink
			for p_idx in range(physicalQubits.N):
				pq = p_list[p_idx]
				cap = physicalQubits.sizes[p_idx]
				edges.append((pq, sink, cap, 0))

			# prepare edges
			start, end, caps, costs = [], [], [], []
			for u, v, c, cs in edges:
				start.append(u)
				end.append(v)
				caps.append(c)
				costs.append(cs * virtualQubits.N * 100)
			supplies = [virtualQubits.N] + [0 for _ in range(virtualQubits.N + physicalQubits.N)] + [-virtualQubits.N]
			
			smcf = min_cost_flow.SimpleMinCostFlow()
			smcf.add_arcs_with_capacity_and_unit_cost(
				np.array(start),
				np.array(end),
				np.array(caps),
				np.array(costs)
			)
			for count, supply in enumerate(supplies):
				smcf.set_node_supply(count, supply)

			# solve
			status = smcf.solve()
			if status != smcf.OPTIMAL:
				print('There was an issue with the min cost flow input.')
				print(f'Status: {status}')
				exit(1)

			# decode
			virtualToPhysical = [-1] * virtualQubits.N
			for i in range(smcf.num_arcs()):
				if(smcf.flow(i) == 0): continue
				vq, pq = smcf.tail(i), smcf.head(i)
				if(vq != source and pq != sink):
					v_idx = vq - v_list[0]
					p_idx = pq - p_list[0]
					virtualToPhysical[v_idx] = p_idx

			# update
			arr = []
			e_idx = 0
			for v_idx in range(virtualQubits.N):
				for p_idx in candidates[v_idx]:
					if(p_idx == virtualToPhysical[v_idx]):
						arr.append(e_idx)
					e_idx += 1
			val = self._eval_cost(arr, potential, interaction)

			if(virtualToPhysical_ans == None or val < val_ans):
				virtualToPhysical_ans = [v for v in virtualToPhysical]
				val_ans = val
		
		return virtualToPhysical_ans

	def solve(self, problem: QubitMappingProblem) -> QubitMapping:
		mappingResult = QubitMapping(problem.physicalDevice)
		for layer_idx in range(problem.numLayers):
			layer = problem.layers[layer_idx]
			candidates = problem.candidates[layer_idx]

			potential: list[float] = []
			cost_swap = problem.physicalDevice.cost.cost_swap
			for x in range(layer.virtualQubits.N):
				for y in candidates[x]:
					p = 0
					if(layer_idx == 0 and problem.left_strength > 0 and problem.left_layer != None):
						p += cost_swap[problem.left_layer.virtualToPhysical[x]][y] * problem.left_strength
					if(layer_idx > 0):
						p += cost_swap[mappingResult.layers[layer_idx - 1].virtualToPhysical[x]][y]
					if(layer_idx == problem.numLayers - 1 and problem.right_strength > 0 and problem.right_layer != None):
						p += cost_swap[y][problem.right_layer.virtualToPhysical[x]] * problem.right_strength
					potential.append(p)

			interaction: list[list[float]] = []
			cost_cnot = problem.physicalDevice.cost.cost_cnot
			cnot_counts = [[0 for _ in range(layer.virtualQubits.N)] for _ in range(layer.virtualQubits.N)]
			for g in layer.virtualGates:
				if(isinstance(g, CXGate)):
					cnot_counts[g.Qubit_src][g.Qubit_dst] += 1
			for src in range(layer.virtualQubits.N):
				for ps_idx in range(len(candidates[src])):
					ps = candidates[src][ps_idx]
					int_arr = []
					for dst in range(layer.virtualQubits.N):
						for pd_idx in range(len(candidates[dst])):
							pd = candidates[dst][pd_idx]
							int_arr.append((cost_cnot[ps][pd] * cnot_counts[src][dst] + cost_cnot[pd][ps] * cnot_counts[dst][src]) / 2)
					interaction.append(int_arr)

			mappingResult.AddLayer(
				QubitMappingLayer(
					layer.virtualQubits,
					layer.virtualGates,
					self._find_mapping(
						layer.virtualQubits, problem.physicalDevice.qubits,
						candidates,
						potential,
						interaction,
						problem.physicalDevice.graph.distanceTo
					)
				)
			)
		return mappingResult