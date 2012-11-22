import os
import numpy
import h5py
import vigra
from lazyflow.roi import roiToSlice
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
from lazyflow.operators import OpTrainRandomForestBlocked, OpValueCache
from ilastik.applets.pixelClassification.opPixelClassification import OpPixelClassification
from ilastik.applets.pixelClassification.pixelClassificationSerializer import PixelClassificationSerializer

import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()

class OpMockPixelClassifier(Operator):
    """
    This class is a simple stand-in for the real pixel classification operator.
    Uses hard-coded data shape and block shape.
    Provides hard-coded outputs.
    """
    name = "OpMockPixelClassifier"

    LabelInputs = InputSlot(optional = True, level=1) # Input for providing label data from an external source

    PredictionsFromDisk = InputSlot( optional = True, level=1 ) # TODO: Actually use this input for something

    NonzeroLabelBlocks = OutputSlot(level=1, stype='object') # A list if slices that contain non-zero label values
    LabelImages = OutputSlot(level=1) # Labels from the user
    
    Classifier = OutputSlot(stype='object')
    
    PredictionProbabilities = OutputSlot(level=1)
    
    FreezePredictions = InputSlot()
    
    LabelNames = OutputSlot()
    LabelColors = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpMockPixelClassifier, self).__init__(*args, **kwargs)

        self.LabelNames.setValue( ["Membrane", "Cytoplasm"] )
        self.LabelColors.setValue( [(255,0,0), (0,255,0)] ) # Red, Green
        
        self._data = []
        self.dataShape = (1,10,100,100,1)
        self.prediction_shape = self.dataShape[:-1] + (2,) # Hard-coded to provide 2 classes
        
        self.FreezePredictions.setValue(False)
        
        self.opClassifier = OpTrainRandomForestBlocked(graph=self.graph, parent=self)
        self.opClassifier.Labels.connect(self.LabelImages)
        self.opClassifier.nonzeroLabelBlocks.connect(self.NonzeroLabelBlocks)
        self.opClassifier.fixClassifier.setValue(False)
        
        self.classifier_cache = OpValueCache(graph=self.graph, parent=self)
        self.classifier_cache.Input.connect( self.opClassifier.Classifier )
        
        p1 = numpy.indices(self.dataShape).sum(0) / 207.0
        p2 = 1 - p1

        self.predictionData = numpy.concatenate((p1,p2), axis=4)
    
    def setupOutputs(self):
        numImages = len(self.LabelInputs)

        self.PredictionsFromDisk.resize( numImages )
        self.NonzeroLabelBlocks.resize( numImages )
        self.LabelImages.resize( numImages )
        self.PredictionProbabilities.resize( numImages )
        self.opClassifier.Images.resize( numImages )

        for i in range(numImages):
            self._data.append( numpy.zeros(self.dataShape) )
            self.NonzeroLabelBlocks[i].meta.shape = (1,)
            self.NonzeroLabelBlocks[i].meta.dtype = object

            self.LabelImages[i].meta.shape = self.dataShape
            self.LabelImages[i].meta.dtype = numpy.float64
            
            # Hard-coded: Two prediction classes
            self.PredictionProbabilities[i].meta.shape = self.prediction_shape
            self.PredictionProbabilities[i].meta.dtype = numpy.float64
            self.PredictionProbabilities[i].meta.axistags = vigra.defaultAxistags('txyzc')
            
            # Classify with random data
            self.opClassifier.Images[i].setValue( numpy.random.random(self.dataShape) )
        
        self.Classifier.connect( self.opClassifier.Classifier )
        
    def setInSlot(self, slot, subindex, roi, value):
        key = roi.toSlice()
        assert slot.name == "LabelInputs"
        self._data[subindex[0]][key] = value
        self.LabelImages[subindex[0]].setDirty(key)
    
    def execute(self, slot, subindex, roi, result):
        key = roiToSlice(roi.start, roi.stop)
        index = subindex[0]
        if slot.name == "NonzeroLabelBlocks":
            # Split into 10 chunks
            blocks = []
            slicing = [slice(0,max) for max in self.dataShape]
            for i in range(10):
                slicing[2] = slice(i*10, (i+1)*10)
                if not (self._data[index][slicing] == 0).all():
                    blocks.append( list(slicing) )

            result[0] = blocks
        if slot.name == "LabelImages":
            result[...] = self._data[index][key]
        if slot.name == "PredictionProbabilities":
            result[...] = self.predictionData[key]
    
    def propagateDirty(self, slot, subindex, roi):
        pass
    
class TestOpMockPixelClassifier(object):
    """
    Quick test for the stand-in operator we're using for the serializer test.
    """
    def test(self):
        g = Graph()
        op = OpMockPixelClassifier(graph=g)
        
        op.LabelInputs.resize( 1 )

        # Create some labels
        labeldata = numpy.zeros(op.dataShape)
        labeldata[:,:,0:5,:,:] = 7
        labeldata[:,:,50:60,:] = 8

        # Slice them into our operator
        op.LabelInputs[0][0:1, 0:10, 0:5,   0:100, 0:1] = labeldata[:,:,0:5,:,:]
        op.LabelInputs[0][0:1, 0:10, 50:60, 0:100, 0:1] = labeldata[:,:,50:60,:,:]

        assert (op._data[0] == labeldata).all()

        nonZeroBlocks = op.NonzeroLabelBlocks[0].value
        assert len(nonZeroBlocks) == 2
        assert nonZeroBlocks[0][2].start == 0
        assert nonZeroBlocks[1][2].start == 50
        
        assert op.Classifier.ready()
        

class TestPixelClassificationSerializer(object):

    def test(self):    
        # Define the files we'll be making    
        testProjectName = 'test_project.ilp'
        # Clean up: Remove the test data files we created last time (just in case)
        for f in [testProjectName]:
            try:
                os.remove(f)
            except:
                pass
    
        # Create an empty project
        with h5py.File(testProjectName) as testProject:
            testProject.create_dataset("ilastikVersion", data=0.6)
            
            # Create an operator to work with and give it some input
            g = Graph()
            op = OpMockPixelClassifier(graph=g)
            operatorToSave = op
            serializer = PixelClassificationSerializer(operatorToSave, 'PixelClassificationTest')
            
            op.LabelInputs.resize( 1 )
    
            # Create some labels
            labeldata = numpy.zeros(op.dataShape)
            labeldata[:,:,0:5,:,:] = 1
            labeldata[:,:,50:60,:] = 2
    
            # Slice them into our operator
            op.LabelInputs[0][0:1, 0:10, 0:5,   0:100, 0:1] = labeldata[:,:,0:5,:,:]
            op.LabelInputs[0][0:1, 0:10, 50:60, 0:100, 0:1] = labeldata[:,:,50:60,:,:]

            # change label names and colors
            op.LabelNames.setValue( ["Label1", "Label2"] )
            op.LabelColors.setValue( [(255,30,30), (30,255,30)] )
            
            # Simulate the predictions changing by setting the prediction output dirty
            op.PredictionProbabilities[0].setDirty(slice(None))
    
            # Enable prediction storage
            serializer.predictionStorageEnabled = True
                
            # Serialize!
            serializer.serializeToHdf5(testProject, testProjectName)
    
            # Check that the prediction data was written to the file
            assert (testProject['PixelClassificationTest/Predictions/predictions0000'][...] == op.PredictionProbabilities[0][...].wait()).all()
            
            # Deserialize into a fresh operator
            operatorToLoad = OpMockPixelClassifier(graph=g)
            deserializer = PixelClassificationSerializer(operatorToLoad, 'PixelClassificationTest')
            deserializer.deserializeFromHdf5(testProject, testProjectName)
    
            # Did the data go in and out of the file without problems?
            assert len(operatorToLoad.LabelImages) == 1
            assert (operatorToSave.LabelImages[0][...].wait() == operatorToLoad.LabelImages[0][...].wait()).all()
            assert (operatorToSave.LabelImages[0][...].wait() == labeldata[...]).all()

            assert operatorToSave.LabelNames.value == operatorToLoad.LabelNames.value
            assert (numpy.array(operatorToSave.LabelColors.value) == numpy.array(operatorToLoad.LabelColors.value)).all()
        
        os.remove(testProjectName)

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)

