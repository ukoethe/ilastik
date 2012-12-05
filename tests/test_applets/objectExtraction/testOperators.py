import unittest
import numpy as np
from lazyflow.graph import Graph
from ilastik.applets.objectExtraction.opObjectExtraction import \
    OpObjectExtraction, OpSegmentationImage

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

    def test_segment(self):
        img = binaryImage()
        self.op.BinaryImage.setValue(img)
        segImg = self.op.SegmentationImage.value
        segImg = segImg.astype(np.int)
        self.assertEquals(segImg.shape, img.shape)
        self.assertTrue(segImg.min() == 0)
        self.assertTrue(segImg.max() == 2)


if __name__ == '__main__':
    unittest.main()
