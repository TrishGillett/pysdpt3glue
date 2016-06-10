#! /usr/bin/env python
""" Test suite.
"""
from __future__ import absolute_import
import sys
import unittest

from . import unittest_neos
from . import unittest_sedumi_writer


def main():
    """ The main function.

    Returns:
      True if all tests are successful.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTest(loader.loadTestsFromModule(unittest_neos))
    suite.addTest(loader.loadTestsFromModule(unittest_sedumi_writer))

    res = unittest.TextTestRunner(verbosity=2).run(suite)
    return res.wasSuccessful()


if __name__ == "__main__":
    try:
        sys.exit(0 if main() else 1)
    except KeyboardInterrupt:
        print "Test canceled."
        sys.exit(-1)
