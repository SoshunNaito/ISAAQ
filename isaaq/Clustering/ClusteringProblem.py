from isaaq.Common.PhysicalDevice import PhysicalDevice

class ClusteringProblem:
    def __init__(self, originalDevice: PhysicalDevice, numClusterDevices: int):
        self.originalDevice = originalDevice
        self.numClusterDevices = numClusterDevices

class ClusteringResult:
    def __init__(
        self,
        numClusterDevices: int,
        clusterDevices: list[PhysicalDevice],
        clusterMappings: list[list[list[int]]]
    ):
        self.numClusterDevices = numClusterDevices
        self.clusterDevices = clusterDevices
        self.clusterMappings = clusterMappings