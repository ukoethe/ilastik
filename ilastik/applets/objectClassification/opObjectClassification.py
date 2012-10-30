import numpy
import h5py
import vigra
import vigra.analysis
import copy

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import Everything, SubRegion, List
from lazyflow.operators.ioOperators.opStreamingHdf5Reader import OpStreamingHdf5Reader
from lazyflow.operators.ioOperators.opInputDataReader import OpInputDataReader
from lazyflow.operators import OperatorWrapper, OpBlockedSparseLabelArray, OpValueCache, \
OpMultiArraySlicer2, OpSlicedBlockedArrayCache, OpPrecomputedInput
from lazyflow.request import Request, Pool
from functools import partial

from ilastik.applets.pixelClassification.opPixelClassification import OpShapeReader, OpMaxValue 

class OpObjectTrain(Operator):
    name = "TrainRandomForestObjects"
    description = "Train a random forest on multiple images"
    category = "Learning"

    #FIXME: both of these should have rtype List. It's not used now, because
    #you can't call setValue on it (because it then calls setDirty with an empty slice and fails)
    
    Labels = InputSlot(level=1)
    Features = InputSlot(stype=Opaque, level =1, rtype=List )
    FixClassifier = InputSlot(stype="bool")
    
    Classifier = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpObjectTrain, self).__init__(*args, **kwargs)
        print "I'm the training operator!!!!!!!!!!!!!!!!!!!!!!"
        #self.progressSignal = OrderedSignal()
        self._forest_count = 1
        # TODO: Make treecount configurable via an InputSlot
        self._tree_count = 100
        self.FixClassifier.setValue(False)

    def setupOutputs(self):
        if self.inputs["FixClassifier"].value == False:
            self.outputs["Classifier"].meta.dtype = object
            self.outputs["Classifier"].meta.shape = (self._forest_count,)
            self.outputs["Classifier"].meta.axistags  = None
            
    #@traceLogged(logger, level=logging.INFO, msg="OpTrainRandomForestBlocked: Training Classifier")
    def execute(self, slot, subindex, roi, result):

        #numImages = len(self.Features)
        
        featMatrix = []
        labelsMatrix = []
        
        for i, labels in enumerate(self.Labels):
            lab = labels[:].wait()
            feats = self.Features[i][0].wait()
            #print "blablablablab"
            #print "len labels:", lab.shape
            counts = numpy.asarray(feats[0]['Count'])
            counts = counts[1:]
            #print "len counts:", counts.shape
            print "here are my labels for i=:", i
            print lab
            print "here are my features for i=:", i
            print feats
            index = numpy.nonzero(lab)
            newlabels = lab[index]
            newfeats = counts[index]
            featMatrix.append(newfeats)
            labelsMatrix.append(newlabels)
        
        
        if len(featMatrix)==0 or len(labelsMatrix)==0:
            print "No labels,no features, can't do anything"
            result[:]=None
        else:
            featMatrix=numpy.concatenate(featMatrix,axis=0)
            labelsMatrix=numpy.concatenate(labelsMatrix,axis=0)
            print "shape featMatrix:", featMatrix.shape, "label matrix:", labelsMatrix.shape
            if len(featMatrix.shape)==1:
                featMatrix.resize(featMatrix.shape+(1,))
            if len(labelsMatrix.shape)==1:
                labelsMatrix.resize(labelsMatrix.shape+(1,))
            try:
                #logger.debug("Learning with Vigra...")
                # train and store self._forest_count forests in parallel
                pool = Pool()

                for i in range(self._forest_count):
                    def train_and_store(number):
                        result[number] = vigra.learning.RandomForest(self._tree_count) 
                        result[number].learnRF(featMatrix.astype(numpy.float32),labelsMatrix.astype(numpy.uint32))
                    req = pool.request(partial(train_and_store, i))

                pool.wait()
                pool.clean()

                #logger.debug("Vigra finished")
            except:
                #logger.error( "ERROR: could not learn classifier" )
                #logger.error( "featMatrix shape={}, max={}, dtype={}".format(featMatrix.shape, featMatrix.max(), featMatrix.dtype) )
                #logger.error( "labelsMatrix shape={}, max={}, dtype={}".format(labelsMatrix.shape, labelsMatrix.max(), labelsMatrix.dtype ) )
                print "couldn't learn classifier"
                raise
        
        return result
        
            

    def propagateDirty(self, slot, subindex, roi):
        if slot is not self.FixClassifier and self.inputs["FixClassifier"].value == False:
            self.outputs["Classifier"].setDirty((slice(0,1,None),))


class OpObjectPredict(Operator):
    name = "OpObjectPredict"
    
    Features = InputSlot(stype=Opaque, rtype=List)
    LabelsCount = InputSlot(stype='integer')
    Classifier = InputSlot()
    
    Predictions = OutputSlot(stype=Opaque)

    def setupOutputs(self):
        
        self.Predictions.meta.shape=(1,)
        self.Predictions.meta.dtype = object
        self.Predictions.meta.axistags = None
        '''
        nimages = len(self.Features)
        self.Predictions.resize(nimages)
        for i in range(nimages):
            self.Predictions[i].meta.shape = (1,)
            self.Predictions[i].meta.dtype = object
            self.Predictions[i].meta.axistags = None
        '''


    def execute(self, slot, subindex, roi, result):
        
        forests=self.inputs["Classifier"][:].wait()

        if forests is None:
            # Training operator may return 'None' if there was no data to train with
            return numpy.zeros(numpy.subtract(roi.stop, roi.start), dtype=numpy.float32)[...]

        #traceLogger.debug("OpPredictRandomForest: Got classifier")        
        #assert RF.labelCount() == nlabels, "ERROR: OpPredictRandomForest, labelCount differs from true labelCount! %r vs. %r" % (RF.labelCount(), nlabels)

        #FIXME FIXME
        #over here, we should really select only the objects in the roi. However, roi of list type doesn't work with setValue, so for now
        #we compute everything.
        features = self.Features[0].wait()
        counts = numpy.asarray(features[0]['Count'])
        print "feature shape for prediction:", counts.shape
        if len(counts.shape)==1:
            counts.resize(counts.shape+(1,))
        
        predictions = [0]*len(forests)
        
        def predict_forest(number):
            predictions[number] = forests[number].predictLabels(counts.astype(numpy.float32))
        
        #t2 = time.time()

        # predict the data with all the forests in parallel
        pool = Pool()

        for i,f in enumerate(forests):
            req = pool.request(partial(predict_forest, i))

        pool.wait()
        pool.clean()

        
        #FIXME we return from here for now, but afterwards we should really average the pool results
        return predictions
        
        
        print len(predictions), predictions[0].shape
        prediction=numpy.dstack(predictions)
        prediction = numpy.average(prediction, axis=2)
        #prediction.shape =  shape[:-1] + (forests[0].labelCount(),)
        print prediction
        return prediction
        
        #prediction = prediction.reshape(*(shape[:-1] + (forests[0].labelCount(),)))

        # If our LabelsCount is higher than the number of labels in the training set,
        # then our results aren't really valid.
        # Duplicate the last label's predictions
        chanslice = slice(min(key[-1].start, forests[0].labelCount()-1), min(key[-1].stop, forests[0].labelCount()))

        t3 = time.time()

        # logger.info("Predict took %fseconds, actual RF time was %fs, feature time was %fs" % (t3-t1, t3-t2, t2-t1))
        return prediction[...,chanslice] # FIXME: This assumes that channel is the last axis

    
    def propagateDirty(self, slot, subindex, roi):
        
        #self.Predictions.setDirty(List(self.Predictions, range(roi.start[0], roi.stop[0]))) 
        self.Predictions.setDirty(roi)

    

class OpObjectClassification(Operator):
    
    name = "OpObjectClassification"
    category = "Top-level"
    
    BinaryImages = InputSlot(level = 1) #Just for display
    InputImages = InputSlot(level = 1)
    ObjectFeatures = InputSlot(stype=Opaque, rtype=List, level=1 )
    LabelsAllowedFlags = InputSlot(stype='bool', level=1) # Specifies which images are permitted to be labeled 
    
    LabelInputs = InputSlot(stype= Opaque, optional = True, level=1) # Input for providing label data from an external source
                                                                    # Labels come in the form of a list, as long as the number
                                                                    # of objects (see also relabeling property of the 
                                                                    # RelabelingLazyflowSourceSink in volumina
    
    FreezePredictions = InputSlot(stype='bool')

    #MaxObjectNumber = InputSlot(level=1, stype = Opaque)

    MaxLabelValue = OutputSlot()
    
    LabelOutputs = OutputSlot(level=1) # Labels from the user. We just give the connected components overlay again
    
    #FIXME: these are temporary, not needed for functionality, but for the labeling gui inteface
    Eraser = OutputSlot()
    DeleteLabel = OutputSlot()
    
    Classifier = OutputSlot()
    PredictionLabels = OutputSlot(level=1) # Classification predictions

    #PredictionProbabilityChannels = OutputSlot(level=2) # Classification predictions, enumerated by channel
    
    def __init__(self, *args, **kwargs):
        super(OpObjectClassification, self).__init__(*args, **kwargs)
        
        self.opInputShapeReader = OperatorWrapper( OpShapeReader, parent=self, graph=self.graph )
        self.opInputShapeReader.Input.connect( self.InputImages )
        
        #self.opMaxLabel = OpMaxListValue(graph=self.graph)
        
        # Set up other label cache inputs
                
        # Initialize the delete input to -1, which means "no label".
        # Now changing this input to a positive value will cause label deletions.
        # (The deleteLabel input is monitored for changes.)
        #self.opLabelArray.inputs["deleteLabel"].setValue(-1)
        
        # Find the highest label in all the label images
        #self.opMaxLabel.Inputs.connect( self.opLabelArray.outputs['maxLabel'] )
    
        #self.opMaxLabel.Inputs.connect(self.LabelInputs)
        
        self.opTrain = OpObjectTrain(graph = self.graph)
        self.opTrain.inputs["Features"].connect(self.ObjectFeatures)
        self.opTrain.inputs['Labels'].connect(self.LabelInputs)
        self.opTrain.inputs['FixClassifier'].setValue(False)
        
        self.opPredict = OperatorWrapper(OpObjectPredict, parent = self, graph = self.graph)
        #self.opPredict = OpObjectPredict(graph = self.graph)
        self.opPredict.inputs["Features"].connect(self.ObjectFeatures)
        self.opPredict.inputs["Classifier"].connect(self.opTrain.outputs["Classifier"])
        self.opPredict.inputs["LabelsCount"].setValue(2)
        
        
        #Connect the outputs
        self.Eraser.setValue(100)
        self.DeleteLabel.setValue(-1)
        #self.MaxObjectNumber.setValue(19)
        self.LabelOutputs.connect( self.InputImages )
        #self.MaxLabelValue.connect( self.opMaxLabel.Output )
        self.MaxLabelValue.setValue(2)
        self.PredictionLabels.connect(self.opPredict.Predictions)
        self.Classifier.connect(self.opTrain.Classifier)
        
        
        def handleNewInputImage( multislot, index, *args ):
            def handleInputReady(slot):
                self.setupCaches( multislot.index(slot) )
                '''
                print "meta info of operator slots:"
                print self.LabelInputs.meta.axistags
                print self.LabelOutputs.meta.axistags
                print self.LabelsAllowedFlags.meta.axistags
                print self.MaxObjectNumber.meta.axistags
                print self.InputImages.meta.axistags
                print self.ObjectFeatures.meta.axistags
                #self.LabelInputs.value.append([])
                '''
            multislot[index].notifyReady(handleInputReady)
                
        self.InputImages.notifyInserted( handleNewInputImage )
    
    
    def setupCaches(self, imageIndex):
        #Setup the label input to correct dimensions
        #print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! calling setup caches"
        
        numImages = len(self.InputImages)
        
        self.LabelInputs.resize(numImages)

        self.LabelInputs[imageIndex].meta.shape = (1,)
        self.LabelInputs[imageIndex].meta.dtype = object
        self.LabelInputs[imageIndex].meta.axistags = None
        '''
        if self.MaxObjectNumber[imageIndex].ready():
            #FIXME: we set it to a list of arrays, because otherwise value only returns the first element
            self.LabelInputs[imageIndex].setValue([numpy.zeros((self.MaxObjectNumber[imageIndex].value+1))])
            print "set up label inputs", self.MaxObjectNumber[imageIndex].value, self.LabelInputs[imageIndex].value
        else:
            self.LabelInputs[imageIndex].setValue([])
        '''
        self.LabelInputs[imageIndex].setValue([numpy.zeros((19,))])
                
    def setupOutputs(self):
        pass
        '''
        if self.Features.ready():
            feats = self.Features[0]
            nobjects = feats[feats.activeNames()[0]].shape[0]
            self.maxObjectNumber.setValue(nobjects)
        '''
    
    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass

    def propagateDirty(self, slot, subindex, roi):
        # Output slots are directly connected to internal operators
        pass 
    
class OpMaxListValue(Operator):
    #For each image, the input is a relabeling vector
    Inputs = InputSlot(level=1) # A list of lists of values
    Output = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpMaxListValue, self).__init__(*args, **kwargs)
        self.Output.meta.shape = (1,)
        self.Output.meta.dtype = object
        self._output = 0
        
    def setupOutputs(self):
        self.updateOutput()
        self.Output.setValue(self._output)

    def execute(self, slot, subindex, roi, result):
        result[0] = self._output
        return result

    def propagateDirty(self, inputSlot, subindex, roi):
        self.updateOutput()
        self.Output.setValue(self._output)

    def updateOutput(self):
        # Return the max value of all our inputs
        maxValue = None
        for i, inputSubSlot in enumerate(self.Inputs):
            # Only use inputs that are actually configured
            if inputSubSlot.ready():
                if len(inputSubSlot.value)>0:
                    curMax = numpy.max(inputSubSlot.value)
                    if maxValue is None:
                        maxValue = curMax
                    else:
                        maxValue = max(maxValue, curMax)
        
        if maxValue is None:
            self._output = 0
        else:
            self._output = maxValue


