from isaaq.Common.PhysicalDevice import PhysicalDevice
from dataclasses import dataclass

@dataclass
class ClusteringProblem:
    originalDevice: PhysicalDevice
    numClusters: int

@dataclass
class ClusteringResult:
    originalDevice: PhysicalDevice
    clusterDevice: PhysicalDevice
    clusters: list[list[int]]