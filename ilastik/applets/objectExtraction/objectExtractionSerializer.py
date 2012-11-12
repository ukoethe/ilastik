from ilastik.applets.base.appletSerializer import AppletSerializer
from lazyflow.rtype import List

class ObjectExtractionSerializer(AppletSerializer):
    """
    """
    SerializerVersion = 0.1
    _featureNames = ['RegionCenter', 'Count']

    def __init__(self, mainOperator, projectFileGroupName):
        super(ObjectExtractionSerializer, self).__init__(
            projectFileGroupName, self.SerializerVersion)
        self.mainOperator = mainOperator

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        op = self.mainOperator.innerOperators[0]
        src = op._mem_h5
        self.deleteIfPresent(topGroup, "SegmentationImage")
        src.copy('/SegmentationImage', topGroup)

        self.deleteIfPresent(topGroup, "samples")
        samples_gr = self.getOrCreateGroup(topGroup, "samples")
        for t in op._opRegFeats._cache.keys():
            t_gr = samples_gr.create_group(str(t))
            for name in self._featureNames:
                t_gr.create_dataset(name=name, data=op._opRegFeats._cache[t][name])

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        dest = self.mainOperator.innerOperators[0]._mem_h5

        del dest['SegmentationImage']
        topGroup.copy('SegmentationImage', dest)

        if "samples" in topGroup.keys():
            cache = {}
            for t in topGroup["samples"].keys():
                cache[int(t)] = dict()
                for name in self._featureNames:
                    if name in topGroup["samples"][t].keys():
                        cache[int(t)][name] = topGroup["samples"][t][name].value
            self.mainOperator.innerOperators[0]._opRegFeats._cache = cache

        # update region count
        slot = self.mainOperator.innerOperators[0].RegionCount
        roi = List(slot, [0])
        self.mainOperator.innerOperators[0]._regionCount(roi)

    def isDirty(self):
        return True

    def unload(self):
        pass
