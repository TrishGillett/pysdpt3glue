#! /usr/bin/env python
from __future__ import absolute_import
import unittest

from . import unittest_neos
from . import unittest_sedumi_writer


def main():
    """ The main function.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTest(loader.loadTestsFromModule(unittest_neos))
    suite.addTest(loader.loadTestsFromModule(unittest_sedumi_writer))

    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print "Test canceled."
