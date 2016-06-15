""" Glue code for solving Cvxpy SDP problems using Matlab's SDPT3.

This package is for you if:
- You have a semidefinite program constructed as a Cvxpy problem
- Your problem has linear and/or semidefinite constraints
  (extension to accommodate second order cone constraints coming soon)
- You want to solve it using SDPT3
- You want to do the solves on your own computer and
  - You have Matlab installed locally
  - SDPT3 is installed
  - You have added the folder containing SDPT3 to your MATLABPATH
- or you want to use SDPT3 on the wonderful NEOS server and
  - You have firefox installed
  - Your .mat's file size isn't over NEOS' file size limit
    (if I recall, this is around 20-25 MB)
"""
from solve import check_output_target
from solve import sdpt3_solve_problem
from solve import sdpt3_solve_mat
from solve import MATLAB
from solve import OCTAVE
from solve import NEOS
from sedumi_writer import write_cvxpy_to_mat
from sedumi_writer import write_sedumi_to_mat
from result import print_summary
