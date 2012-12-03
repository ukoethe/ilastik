import numpy
import h5py
import vigra
import vigra.analysis

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import Everything, SubRegion, List
from lazyflow.operators.ioOperators.opStreamingHdf5Reader import OpStreamingHdf5Reader

from collections import defaultdict

class OpObjectExtraction(Operator):
    name = "Object Extraction"

    #RawData = InputSlot()
    BinaryImage = InputSlot()
    #FeatureNames = InputSlot(stype=Opaque)

    SegmentationImage = OutputSlot()
    ObjectCenterImage = OutputSlot()

    # all of these slots produce a dictionary keyed by integers
    # indexing the time dimension.
    RegionFeatures = OutputSlot(stype=Opaque, rtype=List)
    RegionCenters = OutputSlot(stype=Opaque, rtype=List)
    RegionCounts = OutputSlot(stype=Opaque, rtype=List)
    ObjectCounts = OutputSlot(stype=Opaque, rtype=List)

    def __init__(self, parent = None, graph = None):
        super(OpObjectExtraction, self).__init__(parent=parent,graph=graph)

        self._opSegmentationImage = OpSegmentationImage(parent=self, graph = self.graph)
        self._opSegmentationImage.BinaryImage.connect(self.BinaryImage)

        self._opRegFeats = OpRegionFeatures(parent = self, graph = self.graph)
        self._opRegFeats.SegmentationImage.connect(self._opSegmentationImage.SegmentationImage)

        self._opObjectCenterImage = OpObjectCenterImage(parent=self, graph=self.graph)
        self._opObjectCenterImage.RegionCenters.connect(self._opRegFeats.RegionCenters)

        self._opObjCounts = OpObjectCounts(parent=self, graph=self.graph)
        self._opObjCounts.SegmentationImage.connect(self._opSegmentationImage.SegmentationImage)

        # connect outputs to inner operator
        self.SegmentationImage.connect(self._opSegmentationImage.SegmentationImage)
        self.RegionFeatures.connect(self._opRegFeats.RegionFeatures)
        self.RegionCenters.connect(self._opRegFeats.RegionCenters)
        self.RegionCounts.connect(self._opRegFeats.RegionCounts)
        self.ObjectCounts.connect(self._opObjCounts.ObjectCounts)
        self.ObjectCenterImage.connect(self._opObjectCenterImage.ObjectCenterImage)

    def setupOutputs(self):
        pass

    def execute(self, slot, subindex, roi, result):
        pass

    def propagateDirty(self, inputSlot, subindex, roi):
        pass


class OpSegmentationImage(Operator):
    BinaryImage = InputSlot()
    SegmentationImage = OutputSlot()

    def setupOutputs(self):
        self.SegmentationImage.meta.assignFrom(self.BinaryImage.meta)

    def execute(self, slot, subindex, roi, destination):
        if slot is self.SegmentationImage:
            a = self.BinaryImage.get(roi).wait()
            assert a.ndim == 5
            assert(a.shape[-1] == 1)

            # FIXME: time start may not be 0
            for t in range(a.shape[0]):
                destination[t, ..., 0] = vigra.analysis.labelVolumeWithBackground(a[t, ..., 0])
            return destination

    def propagateDirty(self, slot, subindex, roi):
        if slot is self.BinaryImage:
            self.SegmentationImage.setDirty([])


class OpRegionFeatures(Operator):
    SegmentationImage = InputSlot()
    RegionFeatures = OutputSlot(stype=Opaque, rtype=List)
    RegionCenters = OutputSlot(stype=Opaque, rtype=List)
    RegionCounts = OutputSlot(stype=Opaque, rtype=List)

    def __init__(self, parent=None, graph=None):
        super(OpRegionFeatures, self).__init__(parent=parent,
                                              graph=graph)
        self._cache = {}
        self.fixed = True

        def setshape(s):
            s.meta.shape = (1,)
            s.meta.dtype = object
            s.meta.axistags = None

        setshape(self.RegionFeatures)
        setshape(self.RegionCenters)
        setshape(self.RegionCounts)


    def setupOutputs(self):
        pass

    @staticmethod
    def _callVigra(a, featname):
        labels = numpy.asarray(a, dtype=numpy.uint32)
        data = numpy.asarray(a, dtype=numpy.float32)
        feats = vigra.analysis.extractRegionFeatures(data,
                                                     labels,
                                                     features=[featname],
                                                     ignoreLabel=0)
        return feats

    def _calcFeat(self, featname, roi):
        feats = {}
        for t in roi:
            if t in self._cache:
                feats_at = self._cache[t]
            elif self.fixed:
                feats_at = {featname: numpy.asarray([])}
            else:
                m = self.SegmentationImage.meta
                hasTime = m.axistags.axisTypeCount(vigra.AxisType.Time) > 0
                troi = None
                if hasTime:
                    troi = SubRegion(self.SegmentationImage,
                                     start=[t,] + (len(self.SegmentationImage.meta.shape) - 1) * [0,],
                                     stop=[t+1,] + list(self.SegmentationImage.meta.shape[1:]))
                else:
                    troi = SubRegion(self.SegmentationImage,
                                     start=len(self.SegmentationImage.meta.shape)*[0,],
                                     stop=list(self.SegmentationImage.meta.shape))
                a = self.SegmentationImage.get(troi).wait()

                if hasTime > 0:
                    a = a[0,...,0] # assumes t,x,y,z,c
                else:
                    a = a.squeeze()
                feats_at = self._callVigra(a, featname)
                self._cache[t] = feats_at
            feats[t] = feats_at
        return feats

    def _combine_feats(self, roi, *args):
        result = defaultdict(dict)
        for featname in args:
            feat = self._calcFeat(featname, roi)
            for key, val in feat.iteritems():
                result[key][featname] = val
        return dict(result)

    def execute(self, slot, subindex, roi, result):
        if slot is self.RegionCenters:
            result = self._calcFeat('RegionCenter', roi)
        elif slot is self.RegionCounts:
            result = self._calcFeat('Count', roi)
        elif slot is self.RegionFeatures:
            result = self._combine_feats(roi, 'RegionCenter', 'Count')
        return result

    def propagateDirty(self, slot, subindex, roi):
        def setdirty(slot):
            slot.setDirty(List(slot, range(roi.start[0], roi.stop[0])))
        if slot is self.SegmentationImage:
            setdirty(self.RegionCenters)
            setdirty(self.RegionCounts)
            setdirty(self.RegionFeatures)


class OpObjectCounts(Operator):
    SegmentationImage = InputSlot()
    ObjectCounts = OutputSlot(stype=Opaque, rtype=List)

    def __init__(self, parent=None, graph=None):
        super(OpObjectCounts, self).__init__(parent=parent,
                                              graph=graph)
        def setshape(s):
            s.meta.shape = (1,)
            s.meta.dtype = object
            s.meta.axistags = None

        setshape(self.ObjectCounts)

    def setupOutputs(self):
        pass

    def execute(self, slot, subindex, roi, result):
        if slot is self.ObjectCounts:
            result = {}
            img = self.SegmentationImage.value
            for t, img in enumerate(img):
                result[t] = img.max() + 1
        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot is self.SegmentationImage:
            self.ObjectCounts.setDirty(List(slot, range(roi.start[0], roi.stop[0])))


class OpObjectCenterImage(Operator):
    RegionCenters = InputSlot()
    ObjectCenterImage = OutputSlot()

    @staticmethod
    def __contained_in_subregion(roi, coords):
        b = True
        for i in range(len(coords)):
            b = b and (roi.start[i] <= coords[i] and coords[i] < roi.stop[i])
        return b

    @staticmethod
    def __make_key(roi, coords):
        key = [coords[i] - roi.start[i] for i in range(len(roi.start))]
        return tuple(key)

    def _execute_ObjectCenterImage(self, roi, result):
        result[:] = 0
        tstart, tstop = roi.start[0], roi.stop[0]
        for t in range(tstart, tstop):
            centers = self.RegionCenters([t]).wait()[t]
            centers = numpy.asarray(centers, dtype=numpy.uint32)
            if centers.size:
                centers = centers[1:,:]
            for center in centers:
                x, y, z = center[0:3]
                for dim in (1, 2, 3):
                    for offset in (-1, 0, 1):
                        c = [t, x, y, z, 0]
                        c[dim] += offset
                        c = tuple(c)
                        if self.__contained_in_subregion(roi, c):
                            result[self.__make_key(roi, c)] = 255
        return result
