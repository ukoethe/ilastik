from abc import ABCMeta, abstractmethod
from ilastik import VersionManager
from ilastik.utility.simpleSignal import SimpleSignal
from ilastik.utility.maybe import maybe


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

    # Drop the last comma
    strSlicing = strSlicing[:-1]
    strSlicing += ']'
    return strSlicing

def stringToSlicing(strSlicing):
    """Parse a string of the form '[0:1,2:3,4:5]' into a slicing
    (i.e. list of slices)

    """
    slicing = []
    # Drop brackets
    strSlicing = strSlicing[1:-1]
    sliceStrings = strSlicing.split(',')
    for s in sliceStrings:
        ends = s.split(':')
        start = int(ends[0])
        stop = int(ends[1])
        slicing.append(slice(start, stop))

    return slicing


class SerialSlot(object):
    """
    Wraps a slot and implements the logic for serializing it.

    Has two member variables:

    * slot: the slot to save/load

    * name: name used for the group in the hdf5 file.
        - for level 0 slots, this should just be a string, or None to
          use the slot's name.
        - for level 1 slots, this should be a tuple (groupname,
          substring), or None.

    """
    def __init__(self, slot, name=None):
        self.slot = slot
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


    def _bind(self):
        """Setup so that when slot is dirty, set appropriate dirty
        flag.

        """
        def setDirty():
            self.dirty = True

        def doMulti(self, index):
            self.slot[index].notifyDirty(setDirty())

        if self.slot.level == 0:
            self.slot.notifyDirty(setDirty())
        else:
            slot.notifyInserted(doMulti)


    def serialize(self, group):
        if not self.slot.ready():
            return
        deleteIfPresent(group, self.name)
        if self.slot.level == 0:
            group.create_dataset(self.name, data=self.slot.value)
        else:
            subgroup = group.create_group(self.name)
            for i, subslot in enumerate(self.slot):
                subname = self.subname.format(i)
                subgoup.create_dataset(subname,
                                       data=self.slot[i].value)
        self.dirty = False

    def deserialize(self, group):
        try:
            subgroup = group[name]
        except KeyError:
            pass
        else:
            if slot.level == 0:
                self.slot.setValue(subgroup[:])
            else:
                self.slot.resize(len(subgroup))
                for i, value in enumerate(subgroup):
                    slot[i].setValue(value[:])
        self.dirty = False

    def unload(self):
        if self.slot.level == 0:
            self.slot.disconnect
        else:
            self.slot.resize(0)


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
