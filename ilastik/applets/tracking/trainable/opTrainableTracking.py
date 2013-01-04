import pgmlink
from lazyflow.graph import Operator, InputSlot, OutputSlot

class TrackingGraphEditor( object ):
    @property
    def graph( self ):
        return self._g
    @graph.setter
    def graph( self, g ):
        self._g = g
    

    def __init__( self ):
        self._g = pgmlink.HypothesesGraph()
        self._g.addNodeTraxelMap()

    def addMove( self, label_timestep1, label_timestep2 ):
        label_timestep1 = map(int, label_timestep1)
        label_timestep2 = map(int, label_timestep2)
        print "addMove", label_timestep1, label_timestep2

        # add Move to graph
        from_n = self._g.addNode(label_timestep1[1])
        to_n = self._g.addNode(label_timestep2[1])
        self._g.addArc(from_n, to_n)

        # add Traxels
        from_traxel = pgmlink.Traxel()
        from_traxel.Id = label_timestep1[0]
        from_traxel.Timestep = label_timestep1[1]
        to_traxel = pgmlink.Traxel()
        to_traxel.Id = label_timestep2[0]
        to_traxel.Timestep = label_timestep2[1]

        self._g.getNodeTraxelMap()[from_n] = from_traxel
        self._g.getNodeTraxelMap()[to_n] = to_traxel


class OpTrainableTracking( Operator ):
    LabelImage = InputSlot()
        
    def __init__( self, *args, **kwargs ):
        super(OpTrainableTracking, self).__init__(*args,**kwargs)
        self.graphEditor = TrackingGraphEditor()
