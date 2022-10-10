from itertools import *
from random import *

def GenerateRandomPermutationList(N: int, prod_max: int) -> list[list[int]]:
	size_max = prod_max // (N * N)
	print("GenerateRandomPermutationList: size_max = " + str(size_max))

	F = 1
	for n in range(1, N+1):
		F *= n
		if(F > size_max):
			F = size_max + 1
			break
	
	if(F <= size_max):
		return [list(p) for p in permutations(list(range(N)))]
	else:
		depth = 0
		while((1 << depth) <= N): depth += 1

		ans: list[list[int]] = []
		tree = [0 for i in range(N + 1)]
		for permutation_idx in range(size_max):
			v = [randint(0, i) for i in range(N)][::-1]
			for i in range(N + 1):
				tree[i] = i & -i

			for i in range(N):
				s, x = 0, 0
				for d in range(depth)[::-1]:
					y = x + (1 << d)
					if(y <= N and s + tree[y] <= v[i]):
						s += tree[y]
						x = y
				v[i] = x

				j = v[i] + 1
				while j <= N:
					tree[j] -= 1
					j += j & -j
			ans.append(v)
		
		print("GenerateRandomPermutationList: finished")
		return ans