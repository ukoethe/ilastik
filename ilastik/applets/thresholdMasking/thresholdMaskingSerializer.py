from ilastik.applets.base.appletSerializer import \
    AppletSerializer, SerialSlot

class ThresholdMaskingSerializer(AppletSerializer):
    """
    Serializes the user's pixel feature selections to an ilastik v0.6 project file.
    """
    SerializerVersion = 0.1
    
    def __init__(self, operator, projectFileGroupName):
        slots = [SerialSlot(operator.MinValue),
                 SerialSlot(operator.MaxValue)]
        
        super(ThresholdMaskingSerializer, self).__init__(projectFileGroupName,
                                                         self.SerializerVersion,
                                                         slots=slots)
