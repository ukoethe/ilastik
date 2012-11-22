from ilastik.applets.base.appletSerializer import \
    AppletSerializer, stringToSlicing, slicingToString, \
    deleteIfPresent, SerialSlot, SerialClassifierSlot, SerialBlockSlot, \
    SerialListSlot
from lazyflow.operators import OpH5WriterBigDataset
from lazyflow.operators.ioOperators import OpStreamingHdf5Reader
import threading

class SerialPredictionSlot(SerialSlot):

    def __init__(self, slot, operator, *args, **kwargs):
        super(SerialPredictionSlot, self).__init__(slot, *args, **kwargs)
        self.operator = operator

        self._predictionStorageEnabled = False
        self._predictionStorageRequest = None
        self._predictionsPresent = False

    @property
    def predictionStorageEnabled(self):
        return self._predictionStorageEnabled

    @predictionStorageEnabled.setter
    def predictionStorageEnabled(self, value):
        self._predictionStorageEnabled = value
        if not self._predictionsPresent:
            self.dirty = True

    def cancel(self):
        if self._predictionStorageRequest is not None:
            self.predictionStorageEnabled = False
            self._predictionStorageRequest.cancel()

    def _serialize(self, group):
        """Called when the currently stored predictions are dirty. If
        prediction storage is currently enabled, store them to the
        file. Otherwise, just delete them/

        (Avoid inconsistent project states, e.g. don't allow old
        predictions to be stored with a new classifier.)

        """
        # TODO: progress indicator
        for i,slot in enumerate(self.operator.PredictionsFromDisk):
            slot.disconnect()
        if not self.predictionStorageEnabled:
            return

        predictionDir = group.create_group(self.name)
        failedToSave = False
        try:
            num = len(self.slot)

            for imageIndex in range(num):
                # Have we been cancelled?
                if not self.predictionStorageEnabled:
                    break

                datasetName = self.subname.format(imageIndex)

                # Use a big dataset writer to do this in chunks
                opWriter = OpH5WriterBigDataset(graph=self.operator.graph)
                opWriter.hdf5File.setValue(predictionDir)
                opWriter.hdf5Path.setValue(datasetName)
                opWriter.Image.connect(self.slot[imageIndex])

                # Create the request
                self._predictionStorageRequest = opWriter.WriteImage[...]

                finishedEvent = threading.Event()
                def handleFinish(request):
                    finishedEvent.set()

                def handleCancel(request):
                    self._predictionStorageRequest = None
                    finishedEvent.set()

                # Trigger the write and wait for it to complete or cancel.
                self._predictionStorageRequest.notify(handleFinish)
                self._predictionStorageRequest.onCancel(handleCancel)
                finishedEvent.wait()
        except:
            failedToSave = True
            raise
        finally:
            # If we were cancelled, delete the predictions we just started
            if not self.predictionStorageEnabled or failedToSave:
                deleteIfPresent(predictionDir, datasetName)
                self._predictionsPresent = False
            else:
                # Re-load the operator with the prediction groups we just saved
                self.deserialize(group)

    def deserialize(self, group):
        # override because we need to set self._predictionsPresent
        self._predictionsPresent = self.name in group.keys()
        super(SerialPredictionSlot, self).deserialize(group)

    def _deserialize(self, predictionGroup):
        # Flush the GUI cache of any saved up dirty rois
        if self.operator.FreezePredictions.value == True:
            self.operator.FreezePredictions.setValue(False)
            self.operator.FreezePredictions.setValue(True)

        for imageIndex, datasetName in enumerate(predictionGroup.keys()):
            opStreamer = OpStreamingHdf5Reader(graph=self.operator.graph)
            opStreamer.Hdf5File.setValue(predictionGroup)
            opStreamer.InternalPath.setValue(datasetName)
            self.operator.PredictionsFromDisk[imageIndex].connect(opStreamer.OutputImage)


class PixelClassificationSerializer(AppletSerializer):
    """Encapsulate the serialization scheme for pixel classification
    workflow parameters and datasets.

    """
    SerializerVersion = 0.1

    def __init__(self, operator, projectFileGroupName):
        self.predictionSlot = SerialPredictionSlot(operator.PredictionProbabilities,
                                                   operator,
                                                   name=('Predictions', 'predictions{:04d}'))
        slots = [SerialClassifierSlot(operator.Classifier,
                                      operator.classifier_cache,
                                      name=("ClassifierForests", "Forest{:04d}")),
                 SerialListSlot(operator.LabelNames,
                                transform=str),
                 SerialListSlot(operator.LabelColors),
                 SerialBlockSlot(operator.LabelInputs,
                                 operator.LabelImages,
                                 operator.NonzeroLabelBlocks,
                                 name=('LabelSets', 'labels{:03d}')),
                 self.predictionSlot]


        super(PixelClassificationSerializer, self).__init__(projectFileGroupName,
                                                            self.SerializerVersion,
                                                            slots=slots)

    @property
    def predictionStorageEnabled(self):
        return self.predictionSlot.predictionStorageEnabled

    @predictionStorageEnabled.setter
    def predictionStorageEnabled(self, value):
        self.predictionSlot.predictionStorageEnabled = value

    def cancel(self):
        self.predictionSlot.cancel()


class Ilastik05ImportDeserializer(AppletSerializer):
    """
    Special (de)serializer for importing ilastik 0.5 projects.
    For now, this class is import-only.  Only the deserialize function is implemented.
    If the project is not an ilastik0.5 project, this serializer does nothing.
    """
    SerializerVersion = 0.1

    def __init__(self, topLevelOperator):
        super(Ilastik05ImportDeserializer, self).__init__('', self.SerializerVersion)
        self.mainOperator = topLevelOperator

    def serializeToHdf5(self, hdf5Group, projectFilePath):
        """Not implemented. (See above.)"""
        pass

    def deserializeFromHdf5(self, hdf5File, projectFilePath):
        """If (and only if) the given hdf5Group is the root-level group of an
           ilastik 0.5 project, then the project is imported.  The pipeline is updated
           with the saved parameters and datasets."""
        # The group we were given is the root (file).
        # Check the version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # The pixel classification workflow supports importing projects in the old 0.5 format
        if ilastikVersion == 0.5:
            numImages = len(hdf5File['DataSets'])
            self.mainOperator.LabelInputs.resize(numImages)

            for index, (datasetName, datasetGroup) in enumerate(sorted(hdf5File['DataSets'].items())):
                try:
                    dataset = datasetGroup['labels/data']
                except KeyError:
                    # We'll get a KeyError if this project doesn't have labels for this dataset.
                    # That's allowed, so we simply continue.
                    pass
                else:
                    slicing = [slice(0,s) for s in dataset.shape]
                    self.mainOperator.LabelInputs[index][slicing] = dataset[...]

    def importClassifier(self, hdf5File):
        """
        Import the random forest classifier (if any) from the v0.5 project file.
        """
        # Not yet implemented.
        # The old version of ilastik didn't actually deserialize the
        #  classifier, but it did determine how many trees were used.
        pass

    def isDirty(self):
        """Always returns False because we don't support saving to ilastik0.5 projects"""
        return False

    def unload(self):
        # This is a special-case import deserializer.  Let the real deserializer handle unloading.
        pass

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        assert False

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        # This deserializer is a special-case.
        # It doesn't make use of the serializer base class, which makes assumptions about the file structure.
        # Instead, if overrides the public serialize/deserialize functions directly
        assert False
