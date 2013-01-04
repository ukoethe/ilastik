from ilastik.applets.base.standardApplet import StandardApplet
from ilastik.applets.tracking.trainable.opTrainableTracking import OpTrainableTracking
from ilastik.applets.tracking.trainable.trainableTrackingSerializer import TrainableTrackingSerializer
from ilastik.applets.tracking.trainable.trainableTrackingGui import TrainableTrackingGui

class TrainableTrackingApplet( StandardApplet ):
    def __init__( self, name="Trainable Tracking", workflow=None, projectFileGroupName="TrainableTracking" ):
        super(TrainableTrackingApplet, self).__init__( name=name, workflow=workflow )        
        self._serializableItems = [ TrainableTrackingSerializer(self.topLevelOperator, projectFileGroupName) ]

    @property
    def singleLaneOperatorClass( self ):
        return OpTrainableTracking

    @property
    def broadcastingSlots( self ):
        return []

    @property
    def singleLaneGuiClass( self ):
        return TrainableTrackingGui

    @property
    def dataSerializers(self):
        return self._serializableItems
