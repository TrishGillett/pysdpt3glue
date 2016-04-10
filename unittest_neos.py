# -*- coding: utf-8 -*-
"""
Created on Sun Apr  3 14:56:40 2016

@author: trish
"""

import unittest
import os

import numpy as np

import cvxpy

import solve as slv
import solve_neos as ns
import sedumi_writer as sw
import result as res


class TestSimpleNEOSSolve(unittest.TestCase):
    '''
    Testing simplification of Sedumi problems.
    '''

    def test_hamming(self):
        '''
        Try submitting the .mat for a problem from DIMACS (hamming_7_5_6), to
        test if we can do submission and result extraction in a case where we
        know the .mat isn't the problem.
        '''
        matfile_path = os.path.join('test_data', 'hamming_7_5_6.mat')
        assert os.path.exists(matfile_path), \
            "The DIMACS test problem hamming_7_5_6.mat isn't in the file " + matfile_path
        result = slv.sdpt3_solve_mat(matfile_path, 'neos', discard_matfile=False)
        assert abs(result['primal_z'] + 42.6666661) < 0.01


    @unittest.skip("")
    def test_submission(self):
        '''
        Set up the data for two cases of b (0 or nonzero) and two cases of 'f' (2 or 6)
        '''
        A = 1.*np.array([[1, 0, 0, 0], # X00 = 1
                         [0, 0, 0, 1]]) # X11 = 1
        b = 1.*np.array([1, 1]).reshape(2, 1)
        c = 1.*np.array([0, 1, 0, 0]).reshape(1, 4)
        K = {'l': 0, 's': [2]}

        matfile_target = os.path.join('temp', 'matfile.mat')
        output_target = os.path.join('temp', 'output.txt')
        sw.write_sedumi_to_mat(A, b, c, K, matfile_target)
        msg = ns.neos_solve(matfile_target, output_target=output_target, discard_matfile=True)

        # Process the message
        result = res.make_result_dict(msg)
        print "\n" + res.make_result_summary(result)
        return result




class TestBlackbox(unittest.TestCase):
    '''
    Test the overall process from start to finish
    '''
    def setUp(self):
        self.X = cvxpy.Semidef(3)
        self.constraints = []

        for i in range(3):
            self.constraints += [self.X[i, i] == 1]

        self.constraints += [-0.2 <= self.X[0, 1],
                             self.X[0, 1] <= -0.1,
                             0.4 <= self.X[1, 2],
                             self.X[1, 2] <= 0.5]
        self.temp_folder = "temp"
        if not os.path.exists(self.temp_folder):
            os.makedirs(self.temp_folder)

    def test_min(self):
        '''
        min y s.t.
            -0.2 <= x <= -0.1
            0.4 <= z <=  0.5
            [1  x  y]
            |x  1  z| is PSD
            [y  z  1]
        '''
        matfile_target = os.path.join(self.temp_folder, 'matfile.mat')
        output_target = os.path.join(self.temp_folder, 'output.txt')

        obj = cvxpy.Minimize(self.X[0, 2])
        problem = cvxpy.Problem(obj, self.constraints)
        result = slv.sdpt3_solve_problem(problem, 'neos', matfile_target, output_target=output_target)
#        assert result['primal_z'] == # TODO re-check the actual solution to this
        print result['primal_z']

    @unittest.skip("")
    def test_max(self):
        '''
        max y s.t.
            -0.2 <= x <= -0.1
            0.4 <= z <=  0.5
            [1  x  y]
            |x  1  z| is PSD
            [y  z  1]
        '''
        matfile_target = os.path.join(self.temp_folder, 'matfile.mat')
        output_target = os.path.join(self.temp_folder, 'output.txt')

        obj = cvxpy.Maximize(self.X[0, 2])
        problem = cvxpy.Problem(obj, self.constraints)
        slv.sdpt3_solve_problem(problem, 'neos', matfile_target, output_target=output_target, discard_matfile=False)



if __name__ == '__main__':
    unittest.main()
