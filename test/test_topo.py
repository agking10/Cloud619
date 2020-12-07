import sys
import os.path

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

import unittest
import DCTopo

from mininet.net import Mininet
from mininet.clean import cleanup


class TopoTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        if sys.exc_info != (None, None, None):
            cleanup()

    def run_test(self, k=4):
        # TODO
        pass

    def test_k4(self):
        self.run_test(k=4)

    def test_k8(self):
        self.run_test(k=8)

    def test_k12(self):
        self.run_test(k=12)

    def test_k16(self):
        self.run_test(k=16)

    def test_k24(self):
        self.run_test(k=24)

if __name__ == '__main__':
    unittest.main()
