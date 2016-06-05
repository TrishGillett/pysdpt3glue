# py-sdpt3-glue
[![Code Climate](https://codeclimate.com/github/discardthree/py-sdpt3-glue/badges/gpa.svg)](https://codeclimate.com/github/discardthree/py-sdpt3-glue)
[![Build Status](https://travis-ci.org/discardthree/PySDPT3glue.svg?branch=master)](https://travis-ci.org/discardthree/PySDPT3glue)
[![MIT License](http://img.shields.io/badge/license-MIT-blue.svg?style=flat)](LICENSE)

Glue code for solving Cvxpy SDP problems using Matlab's SDPT3.
This package is for you if:
- You have a semidefinite program constructed as a Cvxpy problem
- Your problem has linear and/or semidefinite constraints (extension to accommodate second order cone constraints coming soon)
- You want to solve it using SDPT3
- You want to do the solves on your own computer and
  - You have Matlab installed locally
  - SDPT3 is installed
  - You have added the folder containing SDPT3 to your MATLABPATH
- or you want to use SDPT3 on the wonderful NEOS server and
  - You have firefox installed
  - Your .mat's file size isn't over NEOS' file size limit (if I recall, this is around 20-25 MB)

The code is intended to work like this:
```
import os

from cvxpy import *
import solve as slv

def demo_example_cvxpy(folder, mode):
    '''
    min y s.t.
    -0.2 <= x <= -0.1
    0.4 <= z <=  0.5
    [1  x  y]
    |x  1  z| is PSD
    [y  z  1]
    '''

    # Declare variables:
    X = Semidef(3)

    # Define objective:
    obj = Minimize(X[0, 2])

    # Define constraints
    constraints = [-0.2 <= X[0, 1], X[0, 1] <= -0.1, 0.4 <= X[1, 2], X[1, 2] <= 0.5]
    constraints += [X[i, i] == 1 for i in range(3)]

    # Construct the Cvxpy problem
    problem = Problem(obj, constraints)

    # Generate filenames
    matfile_target = os.path.join(folder, 'matfile.mat')  # Where to save the .mat file to
    output_target = os.path.join(folder, 'output.txt')    # Where to save the output log

    # Solve the problem, result will be a dictionary with some information about the solve
    result = slv.sdpt3_solve_problem(problem, 'neos', matfile_target, output_target=output_target)

folder = 'temp'  # Where you want to save the .mat and output log.  
mode = 'neos'    # Choose neos, matlab, or octave (octave is VERY beta, expect it to crash and burn)
demo_example_cvxpy(folder, mode)
```
