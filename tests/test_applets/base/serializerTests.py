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
        self.slot.setValue(value)
        self.ss.serialize(self.group)

        rvalue = randArray()
        self.slot.setValue(rvalue)

        self.assertTrue(numpy.any(self.slot.value != value))
        self.ss.deserialize(self.group)
        self.assertTrue(numpy.all(self.slot.value == value))

    def testMultiSlot(self):
        """test whether serialzing and then deserializing works for a
        level-1 slot

        """
        self.mslot.resize(1)
        value = randArray()
        self.mslot[0].setValue(value)
        self.mss.serialize(self.group)

        rvalue = randArray()
        self.mslot[0].setValue(rvalue)

        self.assertTrue(numpy.any(self.mslot[0].value != value))
        self.mss.deserialize(self.group)
        self.assertTrue(numpy.all(self.mslot[0].value == value))


if __name__ == "__main__":
    unittest.main()