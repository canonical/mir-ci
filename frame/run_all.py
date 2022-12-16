#!/usr/bin/python3
import unittest
suite = unittest.TestSuite()
suite.addTest(unittest.TestLoader().discover('.'))
runner = unittest.TextTestRunner()
result = runner.run(suite)
exit(0 if result.wasSuccessful() else 1)
