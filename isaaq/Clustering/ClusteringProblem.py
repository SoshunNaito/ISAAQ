from isaaq.Common.PhysicalDevice import PhysicalDevice

class ClusteringProblem:
    def __init__(self, originalDevice: PhysicalDevice, numClusters: int):
        self.originalDevice = originalDevice
        self.numClusters = numClusters

class ClusteringResult:
    def __init__(
        self,
        originalDevice: PhysicalDevice, clusterDevice: PhysicalDevice,
        clusters: list[list[int]]
    ):
        self.originalDevice = originalDevice
        self.clusterDevice = clusterDevice
        self.clusters = clusters