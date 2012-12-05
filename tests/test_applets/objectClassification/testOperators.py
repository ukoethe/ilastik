import unittest
import numpy as np
from lazyflow.graph import Graph
from ilastik.applets.objectClassification.opObjectClassification import \
    OpToImage

def segImage():
    img = np.zeros((2, 50, 50, 50, 1), dtype=np.int)
    img[0,  0:10,  0:10,  0:10, 0] = 1
    img[0, 20:30, 20:30, 20:30, 0] = 2
    img[1,  0:10,  0:10,  0:10, 0] = 1
    img[1, 10:20, 10:20, 10:20, 0] = 2
    img[1, 20:30, 20:30, 20:30, 0] = 3
    return img


class TestOpToImage(unittest.TestCase):
    def setUp(self):
        g = Graph()
        self.op = OpToImage(graph=g)

    def test(self):
        segimg = segImage()
        map_ = {0 : np.array([10, 20, 30]),
                1 : np.array([40, 50, 60, 70])}
        self.op.Image.setValue(segimg)
        self.op.ObjectMap.setValue(map_)
        img = self.op.Output.value

        self.assertEquals(img[0, 49, 49, 49, 0], 0)
        self.assertEquals(img[1, 49, 49, 49, 0], 0)
        self.assertTrue(np.all(img[0,  0:10,  0:10,  0:10, 0] == 20))
        self.assertTrue(np.all(img[0, 20:30, 20:30, 20:30, 0] == 30))
        self.assertTrue(np.all(img[1,  0:10,  0:10,  0:10, 0] == 50))
        self.assertTrue(np.all(img[1, 10:20, 10:20, 10:20, 0] == 70))
        self.assertTrue(np.all(img[1, 20:30, 20:30, 20:30, 0] == 70))



if __name__ == '__main__':
    unittest.main()
