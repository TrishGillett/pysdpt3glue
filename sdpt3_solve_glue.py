#!/usr/bin/env python
import os

import subprocess
import shlex

import sedumi_writer as sw
import result as res

class MatlabCallError(Exception):
    pass


def matlab_solve(matfile_target, output_target, discard_matfile = True):
    '''
    The .mat is loaded into matlab and the problem is solved with SDPT3.
    Inputs:
      matfile_target: the path to the .mat file containing the Sedumi format problem data.
      output_target: the path we will save the output log message to.
      discard_matfile: if True, deletes the .mat file after the solve finishes.
    Output:
        A dictionary with solve result information.
    '''
    # Generating the .mat file
    run_command = "matlab -r \"SDPT3solve('{0}')\"".format(matfile_target)
    msg = run_matlab_get_output(run_command, output_target)
    
    # Cleanup
    if discard_matfile:
        print "now deleting {0}".format(matfile_target)
        os.remove(matfile_target)
    
    return msg



def run_matlab_get_output(run_command, output_target):
    '''
    Runs the command run_command, saves the output to output_target, and
    returns the output log.
    '''
    # Performing the Matlab solve
    run_command += " -nodisplay -nojvm > {0};".format(output_target)
    tokenized_command = shlex.split(run_command)
    try:
        proc = subprocess.Popen(tokenized_command)
        proc.wait()
    except:
        err_msg = ("Something went wrong with the Matlab command. The command "
                   "run was:\n{0}\nPlease check that the command looks good "
                   "and that the the folder containing SDPT3solve.m is in the "
                   "Matlab path.").format(run_command)
        raise MatlabCallError(err_msg)

    # Reading the log and returning its contents
    with open(output_target, 'r') as myfile:
        msg=myfile.read()

    return msg
