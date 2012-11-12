from ilastik.applets.base.appletSerializer import AppletSerializer

class ObjectClassificationSerializer(AppletSerializer):
    """
    """
    SerializerVersion = 0.1

    def __init__(self, mainOperator, projectFileGroupName):
        super(ObjectClassificationSerializer, self ).__init__(projectFileGroupName, self.SerializerVersion)
        self.mainOperator = mainOperator

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        op = self.mainOperator
        self.deleteIfPresent(topGroup, "Labels")
        labels_gr = self.getOrCreateGroup(topGroup, "Labels")
        for i in range(len(op.LabelInputs)):
            name = str(i)
            labels_gr.create_dataset(name=name, data=op.LabelInputs[0].value[0])


    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        op = self.mainOperator
        if "Labels" in topGroup.keys():
            for key in topGroup["Labels"].keys():
                i = int(key)
                value = topGroup["Labels"][key].value
                op.LabelInputs[i].setValue([value])


    def isDirty(self):
        return True

    def unload(self):
        pass
