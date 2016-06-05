#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  3 14:56:40 2016

@author: trish
"""

import unittest
import os
import shutil

import numpy as np

import cvxpy

import solve as slv
import sedumi_writer as sw
import result as res


class TestSimpleNEOSSolve(unittest.TestCase):
    '''
    Testing simplification of Sedumi problems.
    '''

    @classmethod
    def setUpClass(cls):
        cls.temp_folder = "temp"
        if not os.path.exists(cls.temp_folder):
            os.makedirs(cls.temp_folder)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree("temp")

    def test_hamming(self):
        '''
        Try submitting the .mat for a problem from DIMACS (hamming_7_5_6), to
        test if we can do submission and result extraction in a case where we
        know the .mat isn't the problem.
        '''
        matfile_path = os.path.join('test_data', 'hamming_7_5_6.mat')
        output_path = os.path.join(self.temp_folder, 'hamming_out.txt')
        assert os.path.exists(matfile_path), \
            "There's nothing at the path " + matfile_path
        result = slv.sdpt3_solve_mat(matfile_path,
                                     'neos',
                                     output_target=output_path,
                                     discard_matfile=False)

        self.assertAlmostEqual(result['primal_z'], -42.6666661, places=2)

    def test_submission(self):
        '''
        Set up the data for two cases of b (0 or nonzero) and two cases of 'f' (2 or 6)
        '''
        A = 1.*np.array([[1, 0, 0, 0],  # X00 = 1
                         [0, 0, 0, 1]]) # X11 = 1
        b = 1.*np.array([1, 1]).reshape(2, 1)
        c = 1.*np.array([0, 1, 0, 0]).reshape(1, 4)
        K = {'l': 0., 's': [2.]}

        matfile_target = os.path.join(self.temp_folder, 'matfile.mat')
        output_target = os.path.join(self.temp_folder, 'output.txt')

        sw.write_sedumi_to_mat(A, b, c, K, matfile_target)
        result = slv.sdpt3_solve_mat(matfile_target,
                                     'neos',
                                     output_target=output_target)
        res.print_summary(result)




class TestBlackbox(unittest.TestCase):
    '''
    Test the overall process from start to finish
    '''
    @classmethod
    def setUpClass(cls):
        cls.X = cvxpy.Semidef(3)
        cls.constraints = []

        for i in range(3):
            cls.constraints += [cls.X[i, i] == 1]

        cls.constraints += [cls.X[0, 1] >= -0.2,
                            cls.X[0, 1] <= -0.1,
                            cls.X[1, 2] >= 0.4,
                            cls.X[1, 2] <= 0.5]
        cls.temp_folder = "temp"
        if not os.path.exists(cls.temp_folder):
            os.makedirs(cls.temp_folder)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree('temp')

    def test_min(self):
        '''
        min y s.t.
            -0.2 <= x <= -0.1
            0.4 <= z <=  0.5
            [1  x  y]
            |x  1  z| is PSD
            [y  z  1]
        '''
        matfile_target = os.path.join(self.temp_folder, 'matfilemin.mat')
        output_target = os.path.join(self.temp_folder, 'outputmin.txt')

        obj = cvxpy.Minimize(self.X[0, 2])
        problem = cvxpy.Problem(obj, self.constraints)
        result = slv.sdpt3_solve_problem(problem,
                                         'neos',
                                         matfile_target,
                                         output_target=output_target)
        self.assertAlmostEqual(result['primal_z'], -0.978, places=2)


    @unittest.expectedFailure
    def test_max(self):
        '''
        max y s.t.
            -0.2 <= x <= -0.1
            0.4 <= z <=  0.5
            [1  x  y]
            |x  1  z| is PSD
            [y  z  1]
        '''
        matfile_target = os.path.join(self.temp_folder, 'matfilemax.mat')
        output_target = os.path.join(self.temp_folder, 'outputmax.txt')

        obj = cvxpy.Maximize(self.X[0, 2])
        problem = cvxpy.Problem(obj, self.constraints)
        result = slv.sdpt3_solve_problem(problem,
                                         'neos',
                                         matfile_target,
                                         output_target=output_target)
        # The opt value of the max problem is ~0.871921, but when we retrieved
        # the cvxopt data it was flipped to be a min problem, so for now this
        # is an expected failure until we figure out how to tell from the cvxpy
        # problem whether it's min or max.
        self.assertAlmostEqual(result['primal_z'], 0.872, places=2)




if __name__ == '__main__':
    unittest.main()
