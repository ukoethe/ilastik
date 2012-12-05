import unittest
import numpy as np
from lazyflow.graph import Graph
from ilastik.applets.objectExtraction.opObjectExtraction import \
    OpObjectExtraction, OpSegmentationImage, OpObjectCounts

def binaryImage():
    img = np.zeros((2, 50, 50, 50, 1), dtype=np.float32)
    img[0 ,  0:10,  0:10,  0:10, 0] = 1
    img[0 , 20:30, 20:30, 20:30, 0] = 1
    img[1 , 20:30, 20:30, 20:30, 0] = 1

    return img


class TestOpSegmentationImage(unittest.TestCase):
    def setUp(self):
        g = Graph()
        self.op = OpSegmentationImage(graph=g)
        img = binaryImage()
        self.op.BinaryImage.setValue(img)

    def test_segment(self):
        img = binaryImage()
        segImg = self.op.SegmentationImage.value
        segImg = segImg.astype(np.int)
        self.assertEquals(segImg.shape, img.shape)
        self.assertTrue(segImg.min() == 0)
        self.assertTrue(segImg.max() == 2)


class TestOpObjectCounts(unittest.TestCase):
    def setUp(self):
        g = Graph()
        self.segop = OpSegmentationImage(graph=g)
        self.op = OpObjectCounts(graph=g)
        self.op.SegmentationImage.connect(self.segop.SegmentationImage)
        img = binaryImage()
        self.segop.BinaryImage.setValue(img)

    def test_count(self):
        counts = self.op.ObjectCounts[()].wait()
        self.assertEquals(len(counts), 2)
        self.assertEquals(counts[0], 2)
        self.assertEquals(counts[1], 1)

    def test_count_value(self):
        # for some reason, getting value returns value[0].
        counts = self.op.ObjectCounts.value
        self.assertEquals(len(counts), 2)

    # TODO: test propagateDirty and execute with roi.




if __name__ == '__main__':
    unittest.main()
