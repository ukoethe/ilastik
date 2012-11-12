import numpy
import h5py
import vigra
import vigra.analysis

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import Everything, SubRegion, List
from lazyflow.operators.ioOperators.opStreamingHdf5Reader import OpStreamingHdf5Reader


class OpObjectExtraction(Operator):
    name = "Object Extraction"

    #RawData = InputSlot()
    BinaryImage = InputSlot()
    #FeatureNames = InputSlot(stype=Opaque)

    SegmentationImage = OutputSlot()
    ObjectCenterImage = OutputSlot()

    RegionCenters = OutputSlot(stype=Opaque, rtype=List)
    RegionFeatures = OutputSlot(stype=Opaque, rtype=List)
    RegionCount = OutputSlot(stype=Opaque) #total number of regions

    def __init__(self, parent = None, graph = None):
        super(OpObjectExtraction, self).__init__(parent=parent,graph=graph)

        self._mem_h5 = h5py.File(str(id(self)), driver='core', backing_store=False)
        self._reg_cents = {}

        self._opSegmentationImage = OpSegmentationImage(parent=self, graph = self.graph)
        self._opSegmentationImage.BinaryImage.connect(self.BinaryImage)

        self._opRegCent = OpRegionCenters(parent=self, graph = self.graph)
        self._opRegCent.SegmentationImage.connect(self.SegmentationImage)

        self._opRegFeats = OpRegionFeatures(parent = self, graph = self.graph)
        self._opRegFeats.SegmentationImage.connect(self.SegmentationImage)

        self.RegionFeatures.meta.shape=(1,)
        self.RegionFeatures.meta.dtype=object
        self.RegionFeatures.meta.axistags =None

        self.RegionCount.meta.shape = (1,)
        self.RegionCount.meta.dtype = object
        self.RegionCount.meta.axistags = None
        self.RegionCount.setValue([0])

    def __del__(self):
        self._mem_h5.close()

    def setupOutputs(self):
        self.SegmentationImage.meta.assignFrom(self.BinaryImage.meta)
        self.SegmentationImage.meta.dtype = numpy.uint32
        m = self.SegmentationImage.meta
        self._mem_h5.create_dataset('SegmentationImage', shape=m.shape,
                                    dtype=numpy.uint32, compression=1)

        self._reg_cents = dict.fromkeys(xrange(m.shape[0]),
                                        numpy.asarray([], dtype=numpy.uint16))

        self.ObjectCenterImage.meta.assignFrom(self.BinaryImage.meta)

    def execute(self, slot, subindex, roi, result):

        if slot is self.ObjectCenterImage:
            return self._execute_ObjectCenterImage(roi, result)
        if slot is self.SegmentationImage:
            result = self._mem_h5['SegmentationImage'][roi.toSlice()]
            return result
        if slot is self.RegionCenters:
            res = self._opRegCent.Output.get(roi).wait()
            return res
        if slot is self.RegionFeatures:
            res = self._opRegFeats.Output.get(roi).wait()
            self._regionCount(subindex, roi, res[0])
            return res

        if slot is self.RegionCount:
            result = self._regionCount(subindex, roi)
            return [result]

    def _regionCount(self, subindex, roi, feats=None):
        #FIXME: there has to be some magic here, to extract not only
        #from the first time slice
        if feats is None:
            feats = self._opRegFeats.Output.get(roi).wait()[0]

        # FIXME: do not hardcode key.
        nobjects = len(feats['Count'])
        if self.RegionCount.value[0] != nobjects:
            self.RegionCount.setValue([nobjects])
            self.propagateDirty(self.RegionCount, subindex, None)
        return nobjects

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.RegionCount:
            inputSlot.setDirty(roi)

    def updateSegmentationImage(self):
        m = self.SegmentationImage.meta
        if m.axistags.axisTypeCount(vigra.AxisType.Time) > 0:
            for t in range(m.shape[0]):
                #self.updateSegmentationImageAt(t)
                start = [t,] + (len(m.shape) - 1) * [0,]
                stop = [t+1,] + list(m.shape[1:])
                a = self.BinaryImage.get(SubRegion(self.BinaryImage, start=start, stop=stop)).wait()
                a = a[0,...,0]
                self._mem_h5['SegmentationImage'][t,...,0] = vigra.analysis.labelVolumeWithBackground(a)
                roi = SubRegion(self.SegmentationImage, start=5*(0,), stop=m.shape)
                self.SegmentationImage.setDirty(roi)
        else:
            start = len(m.shape)*[0,]
            stop = list(m.shape)
            a = self.BinaryImage.get(SubRegion(self.BinaryImage,
                                               start=start, stop=stop)).wait()
            a = a.squeeze()
            if len(a.shape)>2:
                self._mem_h5['SegmentationImage'][...,0] = vigra.analysis.labelVolumeWithBackground(a)
            else:
                self._mem_h5['SegmentationImage'][...,0] = vigra.analysis.labelImageWithBackground(a)
            oldshape = self.BinaryImage.meta.shape
            roi = SubRegion(self.SegmentationImage, start=len(oldshape)*(0,),
                            stop=oldshape)
            self.SegmentationImage.setDirty(roi)

    def updateSegmentationImageAt(self, t):
        m = self.SegmentationImage.meta
        start = [t,] + (len(m.shape) - 1) * [0,]
        stop = [t+1,] + list(m.shape[1:])
        a = self.BinaryImage.get(SubRegion(self.BinaryImage,
                                           start=start, stop=stop)).wait()
        a = a[0,...,0]
        self._mem_h5['SegmentationImage'][t,...,0] = vigra.analysis.labelVolumeWithBackground(a)

    def __contained_in_subregion(self, roi, coords):
        b = True
        for i in range(len(coords)):
            b = b and (roi.start[i] <= coords[i] and coords[i] < roi.stop[i])
        return b

    def __make_key(self, roi, coords):

        key = [coords[i]-roi.start[i] for i in range(len(roi.start))]
        return tuple(key)

    def _execute_ObjectCenterImage(self, roi, result):
        result[:] = 0
        m = self.SegmentationImage.meta
        hasTime = m.axistags.axisTypeCount(vigra.AxisType.Time) > 0
        if hasTime:
            for t in range(roi.start[0], roi.stop[0]):
                centers = self.RegionFeatures([t]).wait()[t]['RegionCenter']
                centers = numpy.asarray(centers, dtype=numpy.uint32)
                if centers.size:
                    centers = centers[1:,:]
                for row in range(0,centers.shape[0]):
                    x = centers[row,0]
                    y = centers[row,1]
                    z = centers[row,2]

                    # mark center
                    c =  (t,x,y,z,0)
                    if self.__contained_in_subregion(roi, c):
                        result[self.__make_key(roi,c)] = 255

                    # make the point into a cross
                    c =  (t,x-1,y,z,0)
                    if self.__contained_in_subregion(roi, c):
                        result[self.__make_key(roi, c)] = 255
                    c =  (t,x,y-1,z,0)
                    if self.__contained_in_subregion(roi, c):
                        result[self.__make_key(roi, c)] = 255
                    c =  (t,x,y,z-1,0)
                    if self.__contained_in_subregion(roi, c):
                        result[self.__make_key(roi, c)] = 255

                    c =  (t,x+1,y,z,0)
                    if self.__contained_in_subregion(roi, c):
                        result[self.__make_key(roi, c)] = 255
                    c =  (t,x,y+1,z,0)
                    if self.__contained_in_subregion(roi, c):
                        result[self.__make_key(roi, c)] = 255
                    c =  (t,x,y,z+1,0)
                    if self.__contained_in_subregion(roi, c):
                        result[self.__make_key(roi, c)] = 255
        else:
            centers = self.RegionFeatures([0]).wait()[0]['RegionCenter']
            centers = numpy.asarray(centers, dtype=numpy.uint32)
            if centers.size:
                centers = centers[1:,:]
            for row in range(0,centers.shape[0]):
                x = centers[row,0]
                y = centers[row,1]
                z = centers[row,2]

                # mark center
                c =  (x,y,z,0)
                if self.__contained_in_subregion(roi, c):
                    result[self.__make_key(roi,c)] = 255

                # make the point into a cross
                c =  (x-1,y,z,0)
                if self.__contained_in_subregion(roi, c):
                    result[self.__make_key(roi, c)] = 255
                c =  (x,y-1,z,0)
                if self.__contained_in_subregion(roi, c):
                    result[self.__make_key(roi, c)] = 255
                c =  (x,y,z-1,0)
                if self.__contained_in_subregion(roi, c):
                    result[self.__make_key(roi, c)] = 255

                c =  (x+1,y,z,0)
                if self.__contained_in_subregion(roi, c):
                    result[self.__make_key(roi, c)] = 255
                c =  (x,y+1,z,0)
                if self.__contained_in_subregion(roi, c):
                    result[self.__make_key(roi, c)] = 255
                c =  (x,y,z+1,0)
                if self.__contained_in_subregion(roi, c):
                    result[self.__make_key(roi, c)] = 255

        return result


class OpSegmentationImage(Operator):
    BinaryImage = InputSlot()
    SegmentationImageWithBackground = OutputSlot()

    def setupOutputs(self):
        self.SegmentationImageWithBackground.meta.assignFrom(self.BinaryImage.meta)

    def execute(self, slot, subindex, roi, destination):
        if slot is self.SegmentationImageWithBackground:
            a = self.BinaryImage.get(roi).wait()
            assert(a.shape[0] == 1)
            assert(a.shape[-1] == 1)
            destination[0,...,0] = vigra.analysis.labelVolumeWithBackground(a[0,...,0])
            return destination


class OpRegionFeatures(Operator):
    SegmentationImage = InputSlot()
    Output = OutputSlot(stype=Opaque, rtype=List)

    def __init__(self, parent=None, graph=None):
        super(OpRegionFeatures, self).__init__(parent=parent,
                                              graph=graph)
        self._cache = {}
        self.fixed = True

    def setupOutputs(self):
        pass

    def execute(self, slot, subindex, roi, result):
        if slot is self.Output:
            def extract(a):
                labels = numpy.asarray(a, dtype=numpy.uint32)
                data = numpy.asarray(a, dtype=numpy.float32)
                feats = vigra.analysis.extractRegionFeatures(data,
                                                             labels,
                                                             features=['RegionCenter', 'Count'],
                                                             ignoreLabel=0)
                return feats
                centers = numpy.asarray(feats['RegionCenter'],
                                        dtype=numpy.uint16)
                centers = centers[1:,:]
                return centers

            feats = {}
            for t in roi:
                if t in self._cache:
                    feats_at = self._cache[t]
                elif self.fixed:
                    feats_at = { 'RegionCenter': numpy.asarray([]), 'Count': numpy.asarray([]) }
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
                    feats_at = extract(a)
                    self._cache[t] = feats_at
                feats[t] = feats_at
            return feats

    def propagateDirty(self, slot, subindex, roi):
        if slot is self.SegmentationImage:
            self.Output.setDirty(List(self.Output, range(roi.start[0], roi.stop[0])))


class OpRegionCenters(Operator):
    SegmentationImage = InputSlot()
    Output = OutputSlot(stype=Opaque, rtype=List)

    def __init__(self, parent=None, graph=None):
        super(OpRegionCenters, self).__init__(parent=parent,
                                              graph=graph)
        self._cache = {}
        self.fixed = True

    def setupOutputs(self):
        self.Output.meta.shape = self.SegmentationImage.meta.shape
        self.Output.meta.dtype = self.SegmentationImage.meta.dtype

    def execute(self, slot, subindex, roi, result):
        if slot is self.Output:
            def extract(a):
                labels = numpy.asarray(a, dtype=numpy.uint32)
                data = numpy.asarray(a, dtype=numpy.float32)
                feats = vigra.analysis.extractRegionFeatures(data,
                                                             labels,
                                                             features=['RegionCenter', 'Count'],
                                                             ignoreLabel=0)
                centers = numpy.asarray(feats['RegionCenter'], dtype=numpy.uint16)
                centers = centers[1:,:]
                return centers

            centers = {}
            for t in roi:
                if t in self._cache:
                    centers_at = self._cache[t]
                elif self.fixed:
                    centers_at = numpy.asarray([], dtype=numpy.uint16)
                else:
                    troi = SubRegion(self.SegmentationImage,
                                     start = [t,] + (len(self.SegmentationImage.meta.shape) - 1) * [0,],
                                     stop = [t+1,] + list(self.SegmentationImage.meta.shape[1:]))
                    a = self.SegmentationImage.get(troi).wait()
                    a = a[0,...,0] # assumes t,x,y,z,c
                    centers_at = extract(a)
                    self._cache[t] = centers_at
                centers[t] = centers_at

            return centers

    def propagateDirty(self, slot, subindex, roi):
        if slot is self.SegmentationImage:
            self.Output.setDirty(List(self.Output, range(roi.start[0], roi.stop[0])))
