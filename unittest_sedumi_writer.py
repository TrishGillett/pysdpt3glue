# -*- coding: utf-8 -*-
"""
Created on Thu Apr  7 16:22:17 2016

@author: trish
"""

import unittest

import numpy as np

from sedumi_writer import simplify_sedumi_model


class TestSedumiSimplification(unittest.TestCase):
    '''
    Testing simplification of Sedumi problems.
    '''

    def setUp(self):
        '''
        Set up the data for two cases of b (0 or nonzero) and two cases of 'f' (2 or 6)
        '''
        self.A = 1.*np.array([[1, 2, 0, 0, 0, 0, 0, 0, 0, 0], # x + 2y = 0
                              [0, 1, 1, 0, 0, 0, 0, 0, 0, 0], # y + s1 = 0
                              [1, 0, 0, 0, 0, 0, 0, 0, 1, 0], # x + z21 = 0
                              [0, 0, 1, 0, 0, 0, 0, 0, 1, 1]]) # x + y + z22 = 0
        self.b1 = 1.*np.array([0, 0, 0, 0]).reshape(4, 1)
        self.b2 = 1.*np.array([1, 2, 3, 4]).reshape(4, 1)
        self.c = 1.*np.array([2, 2, 3, 4, 5, 6, 7, 8, 9, 10]).reshape(1, 10)
        self.K1 = {'f': 2, 'l': 4, 's': [2]}
        self.K2 = {'f': 6, 'l': 0, 's': [2]}


    def test_case_zero_2(self):
        '''
        Test the case where b = 0 and 'f' = 2
        '''
        A, b, c, K, offset = simplify_sedumi_model(self.A,
                                                   self.b1,
                                                   self.c,
                                                   self.K1,
                                                   allow_nonzero_b=False)
#        print A, b, c, K
        assert offset == 0
        assert K['f'] == 0
        assert K['l'] == 1
        assert len(K['s']) == 1 and K['s'][0] == 2
        np.allclose(A, np.array([[2., 0., 0., 1., 0.],
                                 [1., 0., 0., 1., 1.]]))
        np.allclose(b, np.array([[0.],
                                 [0.]]))
        np.allclose(c, np.array([[5., 7., 8., 9., 10.]]))


    def test_case_zero_6(self):
        '''
        Test the case where b = 0 and 'f' = 6
        '''
        A, b, c, K, offset = simplify_sedumi_model(self.A,
                                                   self.b1,
                                                   self.c,
                                                   self.K2,
                                                   allow_nonzero_b=False)
#        print A, b, c, K
        assert offset == 0
        assert K['f'] == 3
        assert K['l'] == self.K2['l']
        assert len(K['s']) == 1 and K['s'][0] == 2
        np.allclose(A, np.array([[0., 0., 0., 0., 0., 0.5, 1.]]))
        np.allclose(b, np.array([[0.]]))
        np.allclose(c, np.array([[4., 5., 6., 7., 8., 6.5, 10.]]))




if __name__ == '__main__':
    unittest.main()
