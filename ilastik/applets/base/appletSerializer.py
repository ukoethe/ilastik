from abc import ABCMeta, abstractmethod
from ilastik import VersionManager
from ilastik.utility.simpleSignal import SimpleSignal
from ilastik.utility.maybe import maybe
import os
import tempfile
import vigra
import h5py
import numpy

#######################
# Convenience methods #
#######################

def getOrCreateGroup(parentGroup, groupName):
    """
    Returns parentGorup[groupName], creating first it if necessary.
    """
    try:
        return parentGroup[groupName]
    except KeyError:
        return parentGroup.create_group(groupName)

def deleteIfPresent(parentGroup, name):
    """
    Deletes parentGorup[groupName], if it exists.
    """
    try:
        del parentGroup[name]
    except KeyError:
        pass

def slicingToString(slicing):
    """Convert the given slicing into a string of the form
    '[0:1,2:3,4:5]'

    """
    strSlicing = '['
    for s in slicing:
        strSlicing += str(s.start)
        strSlicing += ':'
        strSlicing += str(s.stop)
        strSlicing += ','

    strSlicing = strSlicing[:-1] # Drop the last comma
    strSlicing += ']'
    return strSlicing

def stringToSlicing(strSlicing):
    """Parse a string of the form '[0:1,2:3,4:5]' into a slicing (i.e.
    list of slices)

    """
    slicing = []
    strSlicing = strSlicing[1:-1] # Drop brackets
    sliceStrings = strSlicing.split(',')
    for s in sliceStrings:
        ends = s.split(':')
        start = int(ends[0])
        stop = int(ends[1])
        slicing.append(slice(start, stop))

    return slicing


class SerialSlot(object):
    """Implements the logic for serializing a slot.

    Arguments
    ---------

    * slot: the slot to save/load

    * name: name used for the group in the hdf5 file.
        - for level 0 slots, this should just be a string, or None to
          use the slot's name.
        - for level 1 slots, this should be a tuple (groupname,
          subname), or None.

          if provided, subname should be able to be formated() with a
          single argument: the index of the subslot.

    * default: the default value when unload() is called. If it is
      None, the slot will just be disconnected (for level 0 slots) or
      resized to length 0 (for multislots)

    * depends: a list of slots which must be ready before this slot
      can be serialized. If None, defaults to [].

    """
    # TODO: only serialize when dirty
    # TODO: ability to force always serialize

    # TODO: wrapper around (de)serialize to perform common tasks like
    # creating a group and setting dirty to False

    def __init__(self, slot, name=None, default=None, depends=None):
        if slot.level > 1:
            # FIXME: recursive serialization, to support arbitrary levels
            raise Exception('slots of levels > 1 not supported')
        self.slot = slot
        self.default = default
        self.depends = maybe(depends, [])
        self.depends.append(slot)
        if name is None:
            if slot.level == 0:
                name = slot.name
            else:
                name = slot.name, "{0}"

        if slot.level == 0:
            self.name = name
        else:
            self.name, self.subname = name

        self.dirty = False
        self._bind()

    def _bind(self, slot=None):
        """Setup so that when slot is dirty, set appropriate dirty
        flag.

        """
        slot = maybe(slot, self.slot)
        def setDirty(*args, **kwargs):
            self.dirty = True

        def doMulti(slot, index, size):
            self.slot[index].notifyDirty(setDirty)

        if slot.level == 0:
            slot.notifyDirty(setDirty)
        else:
            slot.notifyInserted(doMulti)

    def serialize(self, group):
        """Default serializer. May need to be overridden."""
        # TODO: dependencies should be taken care of in lazyflow; i.e.
        # slot.ready() should only return True if all its dependencies
        # are ready.
        for s in self.depends:
            if not s.ready():
                return

        deleteIfPresent(group, self.name)
        if self.slot.level == 0:
            group.create_dataset(self.name, data=self.slot.value)
        else:
            subgroup = group.create_group(self.name)
            for i, subslot in enumerate(self.slot):
                subname = self.subname.format(i)
                subgroup.create_dataset(subname,
                                        data=self.slot[i].value)
        self.dirty = False

    def deserialize(self, group):
        """Default deserializer. May need to be overridden."""
        try:
            subgroup = group[self.name]
        except KeyError:
            pass
        else:
            if self.slot.level == 0:
                val = subgroup[()]
                self.slot.setValue(val)
            else:
                self.slot.resize(len(subgroup))
                for i, g in enumerate(subgroup):
                    val = g[()]
                    self.slot[i].setValue(val)
        self.dirty = False

    def unload(self):
        if self.slot.level == 0:
            if self.default is not None:
                self.slot.setValue(self.default)
            else:
                self.slot.disconnect()
        else:
            self.slot.resize(0)


#######################################################
# some serial slots that are used in multiple applets #
#######################################################

class SerialBlockSlot(SerialSlot):
    """A slot which only saves nonzero blocks."""
    def __init__(self, inslot, outslot, blockslot, name=None, default=None,
                 depends=None):
        super(SerialBlockSlot, self).__init__(inslot, name, default, depends)
        self.inslot = inslot
        self.outslot = outslot
        self.blockslot = blockslot
        self._bind(outslot)

    def serialize(self, group):
        deleteIfPresent(group, self.name)
        mygroup = group.create_group(self.name)

        num = len(self.blockslot)
        for index in range(num):
            subsubname = self.subname.format(index)
            subsubgroup = mygroup.create_group(subsubname)
            nonZeroBlocks = self.blockslot[index].value
            for blockIndex, slicing in enumerate(nonZeroBlocks):
                block = self.outslot[index][slicing].wait()
                blockName = 'block{:04d}'.format(blockIndex)
                subsubgroup.create_dataset(blockName, data=block)
                subsubgroup[blockName].attrs['blockSlice'] = slicingToString(slicing)
        self.dirty = False

    def deserialize(self, group):
        mygroup = group[self.name]
        num = len(mygroup)
        self.inslot.resize(num)

        for index, t in enumerate(sorted(mygroup.items())):
            groupName, labelGroup = t
            for blockData in labelGroup.values():
                slicing = stringToSlicing(blockData.attrs['blockSlice'])
                self.inslot[index][slicing] = blockData[...]
        self.dirty = False


class SerialClassifierSlot(SerialSlot):
    def __init__(self, slot, cacheslot, name=None, default=None, depends=None):
        super(SerialClassifierSlot, self).__init__(slot, name, default, depends)
        self.cacheslot = cacheslot
        if self.name is None:
            self.name = slot.name
            self.subname = "Forest{:04d}"
        self.name, self.subname = name

    def unload(self):
        self.cacheslot.Input.setDirty(slice(None))

    def serialize(self, group):
        deleteIfPresent(group, self.name)
        self.dirty = False
        if not self.slot.ready():
            return

        classifier_forests = self.slot.value

        # Classifier can be None if there isn't any training data yet.
        if classifier_forests is None:
            return
        for forest in classifier_forests:
            if forest is None:
                return

        # Due to non-shared hdf5 dlls, vigra can't write directly to
        # our open hdf5 group. Instead, we'll use vigra to write the
        # classifier to a temporary file.
        tmpDir = tempfile.mkdtemp()
        cachePath = os.path.join(tmpDir, 'tmp_classifier_cache.h5')
        for i, forest in enumerate(classifier_forests):
            forest.writeHDF5(cachePath, '{0}/{1}'.format(self.name,
                                                         self.subname.format(i)))

        # Open the temp file and copy to our project group
        with h5py.File(cachePath, 'r') as cacheFile:
            group.copy(cacheFile[self.name], self.name)

        os.remove(cachePath)
        os.removedirs(tmpDir)

    def deserialize(self, group):
        try:
            classifierGroup = group[self.name]
        except KeyError:
            pass
        else:
            # Due to non-shared hdf5 dlls, vigra can't read directly
            # from our open hdf5 group. Instead, we'll copy the
            # classfier data to a temporary file and give it to vigra.
            tmpDir = tempfile.mkdtemp()
            cachePath = os.path.join(tmpDir, 'tmp_classifier_cache.h5')
            with h5py.File(cachePath, 'w') as cacheFile:
                cacheFile.copy(classifierGroup, self.name)

            forests = []
            for name, forestGroup in sorted(classifierGroup.items()):
                forests.append(vigra.learning.RandomForest(cachePath, '{0}/{1}'.format(self.name, name)))

            os.remove(cachePath)
            os.removedirs(tmpDir)

            # Now force the classifier into our classifier cache. The
            # downstream operators (e.g. the prediction operator) can
            # use the classifier without inducing it to be re-trained.
            # (This assumes that the classifier we are loading is
            # consistent with the images and labels that we just
            # loaded. As soon as training input changes, it will be
            # retrained.)
            self.cacheslot.forceValue(numpy.array(forests))
        finally:
            self.dirty = False


####################################
# the base applet serializer class #
####################################

class AppletSerializer(object):
    """
    Base class for all AppletSerializers.
    """
    # Force subclasses to override abstract methods and properties
    __metaclass__ = ABCMeta

    _base_initialized = False

    #########################
    # Semi-abstract methods #
    #########################

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):

        """Child classes should override this function, if
        necessary.

        """
        pass

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File,
                             projectFilePath):
        """Child classes should override this function, if
        necessary.

        """
        pass

    #############################
    # Base class implementation #
    #############################

    def __init__(self, topGroupName, version, slots=None):
        """Constructor. Subclasses must call this method in their own
        __init__ functions. If they fail to do so, the shell raises an
        exception.

        Parameters:
        * operator: the operator to serialize
        * slots : a list of SerialSlots
        * version: serializer version; for compatability checks
        * topGroupName: name of this applet's data group in the file.
            Defaults to the name of the operator.

        """
        # FIXME: exception if subclass fails to call?
        self.version = version
        self.progressSignal = SimpleSignal() # Signature: emit(percentComplete)
        self._base_initialized = True
        self._dirtyFlags = {}
        self.topGroupName = topGroupName
        self.serialSlots = maybe(slots, [])

    def isDirty(self):
        """Returns true if the current state of this item (in memory)
        does not match the state of the HDF5 group on disk.

        Subclasses only need override this method if ORing the flags
        is not enough.

        """
        return any(list(ss.dirty for ss in self.serialSlots))

    def unload(self):
        """Called if either

        (1) the user closed the project or

        (2) the project opening process needs to be aborted for some
            reason (e.g. not all items could be deserialized
            properly due to a corrupted ilp)

        This way we can avoid invalid state due to a partially loaded
        project.

        """
        for ss in self.serialSlots:
            ss.unload()

    def serializeToHdf5(self, hdf5File, projectFilePath):
        """Serialize the current applet state to the given hdf5 file.

        Subclasses should **not** override this method. Instead,
        subclasses override the 'private' version, *_serializetoHdf5*

        :param hdf5File: An h5py.File handle to the project file,
            which should already be open

        :param projectFilePath: The path to the given file handle.
            (Most serializers do not use this parameter.)

        """
        # Check the overall file version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # Make sure we can find our way around the project tree
        if not VersionManager.isProjectFileVersionCompatible(ilastikVersion):
            return

        self.progressSignal.emit(0)

        topGroup = getOrCreateGroup(hdf5File, self.topGroupName)

        # Set the version
        if 'StorageVersion' not in topGroup.keys():
            topGroup.create_dataset('StorageVersion', data=self.version)
        else:
            topGroup['StorageVersion'][()] = self.version

        try:
            # Do auto serializations
            for ss in self.serialSlots:
                ss.serialize(topGroup)

            # Call the subclass to do remaining work, if any
            self._serializeToHdf5(topGroup, hdf5File, projectFilePath)
        finally:
            self.progressSignal.emit(100)


    def deserializeFromHdf5(self, hdf5File, projectFilePath):
        """Read the the current applet state from the given hdf5File
        handle, which should already be open.

        Subclasses should **not** override this method. Instead,
        subclasses override the 'private' version,
        *_deserializeFromHdf5*

        :param hdf5File: An h5py.File handle to the project file,
            which should already be open

        :param projectFilePath: The path to the given file handle.
            (Most serializers do not use this parameter.)

        """
        # Check the overall file version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # Make sure we can find our way around the project tree
        if not VersionManager.isProjectFileVersionCompatible(ilastikVersion):
            return

        self.progressSignal.emit(0)

        # If the top group isn't there, call initWithoutTopGroup
        try:
            topGroup = hdf5File[self.topGroupName]
            groupVersion = topGroup['StorageVersion'][()]
        except KeyError:
            topGroup = None
            groupVersion = None

        try:
            if topGroup is not None:
                for ss in self.serialSlots:
                    ss.deserialize(topGroup)

                # Call the subclass to do remaining work
                self._deserializeFromHdf5(topGroup, groupVersion, hdf5File, projectFilePath)
            else:
                self.initWithoutTopGroup(hdf5File, projectFilePath)
        finally:
            self.progressSignal.emit(100)

    #######################
    # Optional methods    #
    #######################

    def initWithoutTopGroup(self, hdf5File, projectFilePath):
        """Optional override for subclasses. Called when there is no
        top group to deserialize.

        Gives the applet a chance to inspect the hdf5File or project
        path, even though no top group is present in the file.

        Parameters as the same as in serializeToHdf5()

        """
        pass

    @property
    def base_initialized(self):
        """Do not override this property.

        Used by the shell to ensure that Applet.__init__ was called by
        your subclass.

        """
        return self._base_initialized
