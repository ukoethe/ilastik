from ilastik.applets.base.appletSerializer import AppletSerializer

class ObjectExtractionSerializer(AppletSerializer):
    """
    """
    SerializerVersion = 0.1

    def __init__(self, mainOperator, projectFileGroupName):
        super( ObjectExtractionSerializer, self ).__init__(
            projectFileGroupName, self.SerializerVersion)
        self.mainOperator = mainOperator

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        op = self.mainOperator.innerOperators[0]
        src = op._mem_h5
        self.deleteIfPresent( topGroup, "SegmentationImage")
        src.copy('/SegmentationImage', topGroup)

        self.deleteIfPresent( topGroup, "samples")
        samples_gr = self.getOrCreateGroup( topGroup, "samples" )
        for t in op._opRegFeats._cache.keys():
            t_gr = samples_gr.create_group(str(t))
            t_gr.create_dataset(name="RegionCenter", data=op._opRegFeats._cache[t]['RegionCenter'])
            t_gr.create_dataset(name="Count", data=op._opRegFeats._cache[t]['Count'])

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        dest = self.mainOperator.innerOperators[0]._mem_h5

        del dest['SegmentationImage']
        topGroup.copy('SegmentationImage', dest)

        if "samples" in topGroup.keys():
            cache = {}

            for t in topGroup["samples"].keys():
                cache[int(t)] = dict()
                if 'RegionCenter' in topGroup["samples"][t].keys():
                    cache[int(t)]['RegionCenter'] = topGroup["samples"][t]['RegionCenter'].value
                if 'Count' in topGroup["samples"][t].keys():
                    cache[int(t)]['Count'] = topGroup["samples"][t]['Count'].value
            self.mainOperator.innerOperators[0]._opRegFeats._cache = cache

    def isDirty(self):
        return True

    def unload(self):
        pass
