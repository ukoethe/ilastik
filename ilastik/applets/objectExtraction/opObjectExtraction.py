import numpy
import h5py
import vigra
import vigra.analysis

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import Everything, SubRegion, List
from lazyflow.operators.ioOperators.opStreamingHdf5Reader import OpStreamingHdf5Reader

#import ctracking


class OpLabelImage( Operator ):
    BinaryImage = InputSlot()
    LabelImageWithBackground = OutputSlot()

    def setupOutputs( self ):
        self.LabelImageWithBackground.meta.assignFrom( self.BinaryImage.meta )

    def execute( self, slot, subindex, roi, destination ):
        if slot is self.LabelImageWithBackground:
            a = self.BinaryImage.get(roi).wait()
            assert(a.shape[0] == 1)
            assert(a.shape[-1] == 1)
            destination[0,...,0] = vigra.analysis.labelVolumeWithBackground( a[0,...,0] )
            return destination



class OpRegionFeatures( Operator ):
    LabelImage = InputSlot()
    Output = OutputSlot( stype=Opaque, rtype=List )

    def __init__( self, parent=None, graph=None ):
        super(OpRegionFeatures, self).__init__(parent=parent,
                                              graph=graph)
        self._cache = {}
        self.fixed = True

    def setupOutputs( self ):
        pass
    
    def execute( self, slot, subindex, roi, result ):
        if slot is self.Output:
            def extract( a ):
                labels = numpy.asarray(a, dtype=numpy.uint32)
                data = numpy.asarray(a, dtype=numpy.float32)
                feats = vigra.analysis.extractRegionFeatures(data, labels, features=['RegionCenter', 'Count'], ignoreLabel=0)
                return feats
                centers = numpy.asarray(feats['RegionCenter'], dtype=numpy.uint16)
                centers = centers[1:,:]
                print centers.shape
                return centers
                
            feats = {}
            for t in roi:
                #print "RegionFeatures at", t
                if t in self._cache:
                    feats_at = self._cache[t]
                elif self.fixed:
                    feats_at = { 'RegionCenter': numpy.asarray([]), 'Count': numpy.asarray([]) }
                else:
                    m = self.LabelImage.meta
                    hasTime = m.axistags.axisTypeCount(vigra.AxisType.Time) > 0
                    troi = None
                    if hasTime:
                        troi = SubRegion( self.LabelImage, start = [t,] + (len(self.LabelImage.meta.shape) - 1) * [0,], stop = [t+1,] + list(self.LabelImage.meta.shape[1:]))
                    else:
                        troi = SubRegion( self.LabelImage, start = len(self.LabelImage.meta.shape)*[0,], stop = list(self.LabelImage.meta.shape))
                    a = self.LabelImage.get(troi).wait()
                    
                    #print "a.shape", a.shape
                    if hasTime > 0:
                        a = a[0,...,0] # assumes t,x,y,z,c
                    else:
                        a = a.squeeze()
                    print a.shape, a.dtype
                    feats_at = extract(a)
                    self._cache[t] = feats_at
                feats[t] = feats_at
            #print feats
            return feats
        
    def propagateDirty(self, slot, subindex, roi):
        if slot is self.LabelImage:
            self.Output.setDirty(List(self.Output, range(roi.start[0], roi.stop[0]))) 



class OpRegionCenters( Operator ):
    LabelImage = InputSlot()
    Output = OutputSlot( stype=Opaque, rtype=List )

    
    def __init__( self, parent=None, graph=None ):
        super(OpRegionCenters, self).__init__(parent=parent,
                                              graph=graph)
        self._cache = {}
        self.fixed = True

    def setupOutputs( self ):
        self.Output.meta.shape = self.LabelImage.meta.shape
        self.Output.meta.dtype = self.LabelImage.meta.dtype
    
    def execute( self, slot, subindex, roi, result ):
        if slot is self.Output:
            def extract( a ):
                labels = numpy.asarray(a, dtype=numpy.uint32)
                data = numpy.asarray(a, dtype=numpy.float32)
                feats = vigra.analysis.extractRegionFeatures(data, labels, features=['RegionCenter', 'Count'], ignoreLabel=0)
                centers = numpy.asarray(feats['RegionCenter'], dtype=numpy.uint16)
                centers = centers[1:,:]
                return centers
                
            centers = {}
            for t in roi:
                print "RegionCenters at", t
                if t in self._cache:
                    centers_at = self._cache[t]
                elif self.fixed:
                    centers_at = numpy.asarray([], dtype=numpy.uint16)
                else:
                    troi = SubRegion( self.LabelImage, start = [t,] + (len(self.LabelImage.meta.shape) - 1) * [0,], stop = [t+1,] + list(self.LabelImage.meta.shape[1:]))
                    a = self.LabelImage.get(troi).wait()
                    a = a[0,...,0] # assumes t,x,y,z,c
                    centers_at = extract(a)
                    self._cache[t] = centers_at
                centers[t] = centers_at

            return centers
        
    def propagateDirty(self, slot, subindex, roi):
        if slot is self.LabelImage:
            self.Output.setDirty(List(self.Output, range(roi.start[0], roi.stop[0]))) 

class OpObjectExtraction( Operator ):
    name = "Object Extraction"

    #RawData = InputSlot()
    BinaryImage = InputSlot()
    #FeatureNames = InputSlot( stype=Opaque )

    LabelImage = OutputSlot()
    ObjectCenterImage = OutputSlot()
    
    RegionCenters = OutputSlot( stype=Opaque, rtype=List )
    RegionFeatures = OutputSlot( stype=Opaque, rtype=List )
    RegionCount = OutputSlot( stype=Opaque ) #total number of regions

    def __init__( self, parent = None, graph = None ):
        super(OpObjectExtraction, self).__init__(parent=parent,graph=graph)

        self._mem_h5 = h5py.File(str(id(self)), driver='core', backing_store=False)
        self._reg_cents = {}

        self._opLabelImage = OpLabelImage( graph = graph )
        self._opLabelImage.BinaryImage.connect( self.BinaryImage )

        self._opRegCent = OpRegionCenters( graph = graph )
        self._opRegCent.LabelImage.connect( self.LabelImage )

        self._opRegFeats = OpRegionFeatures( graph = graph )
        self._opRegFeats.LabelImage.connect( self.LabelImage )
        
        self.RegionCount.meta.shape = (1,)
        self.RegionCount.meta.dtype = object
        self.RegionCount.meta.axistags = None
        self.RegionCount.setValue([0])

    
    def __del__( self ):
        self._mem_h5.close()

    def setupOutputs(self):
        self.LabelImage.meta.assignFrom(self.BinaryImage.meta)
        self.LabelImage.meta.dtype = numpy.uint32
        m = self.LabelImage.meta
        self._mem_h5.create_dataset( 'LabelImage', shape=m.shape, dtype=numpy.uint32, compression=1 )

        self._reg_cents = dict.fromkeys(xrange(m.shape[0]), numpy.asarray([], dtype=numpy.uint16))
        
        self.ObjectCenterImage.meta.assignFrom(self.BinaryImage.meta)
        #self.RegionCount.setValue(0)
        
    
    def execute(self, slot, subindex, roi, result):
        
        if slot is self.ObjectCenterImage:
            return self._execute_ObjectCenterImage( roi, result )
        if slot is self.LabelImage:
            #print "pulling from label image, roi:", roi, "subindex:", subindex
            result = self._mem_h5['LabelImage'][roi.toSlice()]
            return result
        if slot is self.RegionCenters:
            res = self._opRegCent.Output.get( roi ).wait()
            return res
        if slot is self.RegionFeatures:
            res = self._opRegFeats.Output.get( roi ).wait()
            return res
        if slot is self.RegionCount:
            print "AAAAAAAAAAAAAAAAAAAAAAAa, retrieving object count"
            res = self._opRegCent.Output.get( roi ).wait()
            #FIXME: there has to be some magic here, to extract not only from the first time slice
        
            feats = res[0]
            nobjects = feats[feats.activeNames()[0]].shape[0]            
            self.RegionCount.setValue([nobjects])
            result[0]=nobjects
            return result
            
            

    def propagateDirty(self, inputSlot, subindex, roi):
        raise NotImplementedError

    def updateLabelImage( self ):
        m = self.LabelImage.meta
        if m.axistags.axisTypeCount(vigra.AxisType.Time) > 0:
            for t in range(m.shape[0]):
                print "Calculating LabelImage at", t
                #self.updateLabelImageAt(t)
                start = [t,] + (len(m.shape) - 1) * [0,]
                stop = [t+1,] + list(m.shape[1:])
                a = self.BinaryImage.get(SubRegion(self.BinaryImage, start=start, stop=stop)).wait()
                a = a[0,...,0]
                self._mem_h5['LabelImage'][t,...,0] = vigra.analysis.labelVolumeWithBackground( a )
                roi = SubRegion(self.LabelImage, start=5*(0,), stop=m.shape)
                self.LabelImage.setDirty(roi)
        else:
            start = len(m.shape)*[0,]
            stop = list(m.shape)
            a = self.BinaryImage.get(SubRegion(self.BinaryImage, start=start, stop=stop)).wait()
            a = a.squeeze()
            if len(a.shape)>2:
                self._mem_h5['LabelImage'][...,0] = vigra.analysis.labelVolumeWithBackground( a )
            else:
                self._mem_h5['LabelImage'][...,0] = vigra.analysis.labelImageWithBackground( a )
            oldshape = self.BinaryImage.meta.shape
            roi = SubRegion(self.LabelImage, start=len(oldshape)*(0,), stop=oldshape)
            self.LabelImage.setDirty(roi)
            

    def updateLabelImageAt( self, t ):
        m = self.LabelImage.meta
        print "Calculating LabelImage at", t
        start = [t,] + (len(m.shape) - 1) * [0,]
        stop = [t+1,] + list(m.shape[1:])
        a = self.BinaryImage.get(SubRegion(self.BinaryImage, start=start, stop=stop)).wait()
        a = a[0,...,0]
        print a.shape, a.dtype
        self._mem_h5['LabelImage'][t,...,0] = vigra.analysis.labelVolumeWithBackground( a )

    def __contained_in_subregion( self, roi, coords ):
        b = True
        for i in range(len(coords)):
            b = b and (roi.start[i] <= coords[i] and coords[i] < roi.stop[i])
        return b

    def __make_key( self, roi, coords ):
        
        key = [coords[i]-roi.start[i] for i in range(len(roi.start))]
        return tuple(key)
        
                
    
    def _execute_ObjectCenterImage( self, roi, result ):
        result[:] = 0
        m = self.LabelImage.meta
        hasTime = m.axistags.axisTypeCount(vigra.AxisType.Time) > 0
        if hasTime:
            for t in range(roi.start[0], roi.stop[0]):
                centers = self.RegionFeatures( [t] ).wait()[t]['RegionCenter']
                centers = numpy.asarray( centers, dtype=numpy.uint32)
                if centers.size:
                    centers = centers[1:,:]
                for row in range(0,centers.shape[0]):
                    x = centers[row,0]
                    y = centers[row,1]
                    z = centers[row,2]
                    
                    # mark center
                    c =  (t,x,y,z,0)
                    if self.__contained_in_subregion( roi, c ): 
                        result[self.__make_key(roi,c)] = 255
    
                    # make the point into a cross
                    c =  (t,x-1,y,z,0)
                    if self.__contained_in_subregion( roi, c ):
                        result[self.__make_key(roi, c)] = 255
                    c =  (t,x,y-1,z,0)
                    if self.__contained_in_subregion( roi, c ):
                        result[self.__make_key(roi, c)] = 255
                    c =  (t,x,y,z-1,0)
                    if self.__contained_in_subregion( roi, c ):
                        result[self.__make_key(roi, c)] = 255
    
                    c =  (t,x+1,y,z,0)
                    if self.__contained_in_subregion( roi, c ):
                        result[self.__make_key(roi, c)] = 255
                    c =  (t,x,y+1,z,0)
                    if self.__contained_in_subregion( roi, c ):
                        result[self.__make_key(roi, c)] = 255
                    c =  (t,x,y,z+1,0)
                    if self.__contained_in_subregion( roi, c ):
                        result[self.__make_key(roi, c)] = 255
        else:
            centers = self.RegionFeatures([0]).wait()[0]['RegionCenter']
            centers = numpy.asarray( centers, dtype=numpy.uint32)
            if centers.size:
                centers = centers[1:,:]
            for row in range(0,centers.shape[0]):
                x = centers[row,0]
                y = centers[row,1]
                z = centers[row,2]
                
                # mark center
                c =  (x,y,z,0)
                if self.__contained_in_subregion( roi, c ): 
                    result[self.__make_key(roi,c)] = 255
                    
                # make the point into a cross
                c =  (x-1,y,z,0)
                if self.__contained_in_subregion( roi, c ):
                    result[self.__make_key(roi, c)] = 255
                c =  (x,y-1,z,0)
                if self.__contained_in_subregion( roi, c ):
                    result[self.__make_key(roi, c)] = 255
                c =  (x,y,z-1,0)
                if self.__contained_in_subregion( roi, c ):
                    result[self.__make_key(roi, c)] = 255

                c =  (x+1,y,z,0)
                if self.__contained_in_subregion( roi, c ):
                    result[self.__make_key(roi, c)] = 255
                c =  (x,y+1,z,0)
                if self.__contained_in_subregion( roi, c ):
                    result[self.__make_key(roi, c)] = 255
                c =  (x,y,z+1,0)
                if self.__contained_in_subregion( roi, c ):
                    result[self.__make_key(roi, c)] = 255
                
        return result
