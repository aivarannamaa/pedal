import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pedal.report import *

class TestCode(unittest.TestCase):

    def test_gently(self):
        clear_report()
        gently('You should always create unit tests.')
        
        self.assertEqual(len(get_all_feedback()), 1)

if __name__ == '__main__':
    unittest.main(buffer=False)