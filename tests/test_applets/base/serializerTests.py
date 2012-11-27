import os
import numpy
import numpy.testing
import h5py
import vigra
import unittest
import shutil
import tempfile
from lazyflow.roi import roiToSlice
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
from lazyflow.operators import OpTrainRandomForestBlocked, OpValueCache

from ilastik.applets.base.appletSerializer import SerialSlot

class OpMock(Operator):
    """A simple operator for testing serializers."""
    name = "OpMock"
    TestSlot = InputSlot(name="TestSlot")
    TestMultiSlot = InputSlot(name="TestMultiSlot", level=1)

    def __init__(self, *args, **kwargs):
        super(OpMock, self).__init__(*args, **kwargs)

    def propagateDirty(self, slot, subindex, roi):
        pass


def randArray():
    return numpy.random.randn(10, 10)


class TestSerialSlot(unittest.TestCase):
    def setUp(self):
        g = Graph()
        operator = OpMock(graph=g)

        # slots and serial slots
        self.slot = operator.TestSlot
        self.ss = SerialSlot(self.slot)
        self.mslot = operator.TestMultiSlot
        self.mss = SerialSlot(self.mslot)

        # project file
        self.tmpDir = tempfile.mkdtemp()
        self.projectFilePath = os.path.join(self.tmpDir, "tmp_project.ilp")
        self.project = h5py.File(self.projectFilePath)
        self.group = self.project.create_group("AppletGroup")

    def tearDown(self):
        self.project.close()
        shutil.rmtree(self.tmpDir)

    def testSlot(self):
        """test whether serialzing and then deserializing works for a
        level-0 slot

        """
        value = randArray()
        rvalue = randArray()
        self.slot.setValue(value)
        self.assertTrue(self.ss.dirty)
        self.ss.serialize(self.group)
        self.assertTrue(not self.ss.dirty)
        self.slot.setValue(rvalue)
        self.assertTrue(self.ss.dirty)
        self.assertTrue(numpy.any(self.slot.value != value))
        self.ss.deserialize(self.group)
        self.assertTrue(numpy.all(self.slot.value == value))
        self.assertTrue(not self.ss.dirty)

    def testMultiSlot(self):
        """test whether serialzing and then deserializing works for a
        level-1 slot

        """
        value = randArray()
        rvalue = randArray()
        self.mslot.resize(1)
        self.mslot[0].setValue(value)
        self.assertTrue(self.mss.dirty)
        self.mss.serialize(self.group)
        self.assertTrue(not self.mss.dirty)
        self.mslot[0].setValue(rvalue)
        self.assertTrue(self.mss.dirty)
        self.assertTrue(numpy.any(self.mslot[0].value != value))
        self.mss.deserialize(self.group)
        self.assertTrue(numpy.all(self.mslot[0].value == value))
        self.assertTrue(not self.mss.dirty)


if __name__ == "__main__":
    unittest.main()