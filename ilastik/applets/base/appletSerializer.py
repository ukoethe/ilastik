from abc import ABCMeta, abstractmethod
from ilastik import VersionManager
from ilastik.utility.simpleSignal import SimpleSignal
from ilastik.utility.maybe import maybe

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

    ####################
    # Abstract methods #
    ####################

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
        raise NotImplementedError

    #############################
    # Base class implementation #
    #############################

    def __init__(self, operator, version, autoSlots=None,
                 unloadSlots=None, topGroupName=None):
        """Constructor. Subclasses must call this method in their own
        __init__ functions. If they fail to do so, the shell raises an
        exception.

        Parameters:
        * operator: the operator to serialize
        * version: serializer version; for compatability checks
        * autoSlots:  list of slots to be automatically serialized
        * unloadSlots: list of slots to be automatically unloaded
        * topGroupName: name of this applet's data group in the file.
            Defaults to the name of the operator.

        """
        # FIXME: exception if subclass fails to call?
        self._version = version
        self.progressSignal = SimpleSignal() # Signature: emit(percentComplete)
        self._base_initialized = True
        self.operator = operator
        self._dirtyFlags = {}

        # TODO: slot verification
        self.autoSlots = maybe(autoslots, [])
        self.unloadSlots = maybe(unloadSlots, [])
        self.topGroupName = maybe(topGroupName, operator.name)

        self._setupAuto()

    def _setDirty(name):
        self._dirtyFlags[name] = True

    def bindSlot(self, slot, name):
        """Setup so that when slot is dirty, set appropriate dirty
        flag.

        """
        def _doSingle(slot, name):
            slot.notifyDirty(bind(self.setDirty, name))

        def _doMulti(slot, name, index):
            _doSingle(slot[index], name)

        if slot.level == 0:
            _doSingle(slot, name)
        else:
            slot.notifyInserted(bind(_doMulti, slot, name))

    def self._setupAuto(self):
        for slot in self.autoSlots:
            self._dirtyFlags[slot.name] = False
            self.bindSlot(slot, slot.name)

    def isDirty(self):
        """Returns true if the current state of this item (in memory)
        does not match the state of the HDF5 group on disk.

        Subclasses only need override this method if ORing the flags
        is not enough.

        """
        return any(self._dirtyFlags.values())

    def unload(self):
        """Called if either

        (1) the user closed the project or

        (2) the project opening process needs to be aborted for some
            reason (e.g. not all items could be deserialized
            properly due to a corrupted ilp)

        This way we can avoid invalid state due to a partially loaded
        project.

        """
        for slot in self.unloadSlots:
            if slot.level == 0:
                slot.disconnect()
            else:
                slot.resize(0)

    def _autoSerialize(self, slot, group):
        pass

    def _autoDeserialize(self, slot, group):
        pass

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

        topGroup = self.getOrCreateGroup(hdf5File, self.topGroupName)

        # Set the version
        if 'StorageVersion' not in topGroup.keys():
            topGroup.create_dataset('StorageVersion', data=self._version)
        else:
            topGroup['StorageVersion'][()] = self._version

        try:
            # Do auto serializations
            for slot in self.autoSlots:
                self._autoSerialize(slot, topGroup)

            # Call the subclass to do remaining work
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
                # Do auto deserializations
                for slot in self.autoSlots:
                    self._autoDeserialize(slot, topGroup)

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

    #######################
    # Convenience methods #
    #######################

    @staticmethod
    def getOrCreateGroup(parentGroup, groupName):
        """
        Convenience helper.
        Returns parentGorup[groupName], creating first it if necessary.
        """
        try:
            return parentGroup[groupName]
        except KeyError:
            return parentGroup.create_group(groupName)

    @staticmethod
    def deleteIfPresent(parentGroup, name):
        """
        Convenience helper.
        Deletes parentGorup[groupName], if it exists.
        """
        try:
            del parentGroup[name]
        except KeyError:
            pass

    @staticmethod
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

    @staticmethod
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

    @property
    def version(self):
        """Return the version of the serializer itself."""
        return self._version

    @property
    def topGroupName(self):
        return self._topGroupName

    @property
    def base_initialized(self):
        """Do not override this property.

        Used by the shell to ensure that Applet.__init__ was called by
        your subclass.

        """
        return self._base_initialized
