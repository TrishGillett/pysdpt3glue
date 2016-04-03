#!/usr/bin/env python
import os

import subprocess
import shlex

import sdpt3_writer as sw
from result import make_result_dict


def solve_with_SDPT3(P, matfile_target, output_target, discard_matfile = True):
    '''
    Inputs:
      P: a cvxpy problem
      matfile_target: the absolute path we will save the .mat file to.
      output_target: the absolute path we will save the output log message to.
      discard_matfile: if True, deletes the .mat file after the solve finishes.
    Output:
        an instance of the SDPT3Result object.
    '''
    # Generating the .mat file
    P_data = P.cvxpy_get_data('CVXOPT')
    sw.makeSDPT3Model(P_data, matfile_target)
    
    # Performing the Matlab solve
    try:
        run_command = "matlab -r \"SDPT3solve('{0}')\" -nodisplay -nojvm > {1};".format(matfile_target, output_target)
        tokenized_command = shlex.split(run_command)
        
        proc = subprocess.Popen(tokenized_command)
        proc.wait()
    except:
        raise Exception("Something went wrong with the Matlab solve.  The command was:\n",
                        run_command,
                        "\nPlease check that the command looks good and that the the folder containing SDPT3solve.m is in the Matlab path.")

    # Reading the log and producing the result
    with open(output_target, 'r') as myfile:
        msg=myfile.read()
    result = make_result_dict(msg)
    
    # Cleanup
    if discard_matfile:
        print "now deleting {0}".format(matfile_target)
        os.remove(matfile_target)
    
    # Print a summary statement and return
    print "\n" + make_result_summary(result_dict)
    return result

