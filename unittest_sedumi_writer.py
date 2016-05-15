# -*- coding: utf-8 -*-
"""
Created on Thu Apr  7 16:22:17 2016

@author: trish
"""

import unittest

import numpy as np
import scipy

import sedumi_writer as sw


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
        self.K1 = {'f': 2, 'l': 4, 'q': [], 's': [2]}
        self.K2 = {'f': 6, 'l': 0, 'q': [], 's': [2]}


    def test_case_zero_2(self):
        '''
        Test the case where b = 0 and 'f' = 2
        '''
        A, b, c, K, offset = sw.simplify_sedumi_model(self.A,
                                                      self.b1,
                                                      self.c,
                                                      self.K1,
                                                      allow_nonzero_b=False)
        assert offset == 0
        assert K['f'] == 0
        assert K['l'] == 1
        assert len(K['s']) == 1 and K['s'][0] == 2
        
        assert np.allclose(A, np.array([[2., 0., 0.5, 0.5, 0.],
                                        [1., 0., 0.5, 0.5, 1.]])), "A was {0}".format(A)
        assert np.allclose(b, np.array([[0.],
                                        [0.]])), "b was {0}".format(b)
        assert np.allclose(c, np.array([[5., 7., 8.5, 8.5, 10.]])), "c was {0}".format(c)


    def test_case_zero_6(self):
        '''
        Test the case where b = 0 and 'f' = 6
        '''
        A, b, c, K, offset = sw.simplify_sedumi_model(self.A,
                                                      self.b1,
                                                      self.c,
                                                      self.K2,
                                                      allow_nonzero_b=False)
        assert offset == 0
        assert K['f'] == 3
        assert K['l'] == self.K2['l']
        assert len(K['s']) == 1 and K['s'][0] == 2
        assert np.allclose(A, np.array([[0., 0., 0., 0., 0.25, 0.25, 1.]])), "A was {0}".format(A)
        assert np.allclose(b, np.array([[0.]])), "b was {0}".format(b)
        assert np.allclose(c, np.array([[4., 5., 6., 7., 7.25, 7.25, 10.]])), "c was {0}".format(c)


class TestSWHelpers(unittest.TestCase):
    '''
    Testing helper functions used in sedumi problem writing.
    '''

    def test_sparsify_tall_mat(self):
        '''
        Test that our sparsify_tall_mat method gets the same result as normal
        sparsification.
        '''
        M = np.random.random(size=(1000,1000))
        M1 = sw.sparsify_tall_mat(M, block_height=5)
        M2 = scipy.sparse.coo_matrix(M)
        self.assertEqual((M1!=M2).nnz, 0)

    def test_clean_K_dims(self):
        '''
        Test that the clean_K_dims method changes all integer components of K to floats
        '''
        K = sw.clean_K_dims({'d': 7, 'p': [4], 'q': [3, 5]})
        for key in K:
            self.assertIsInstance(K['p'], list)
            self.assertIsInstance(K['q'], list)
            
            self.assertIsInstance(K['d'], (np.float32, np.float64, float))
            self.assertIsInstance(K['p'][0], (np.float32, np.float64, float))
            self.assertIsInstance(K['q'][1], (np.float32, np.float64, float))
            



if __name__ == '__main__':
    unittest.main()
