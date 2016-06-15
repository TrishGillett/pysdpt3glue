#!/usr/bin/env python
'''
Methods that run code on Matlab or Octave.
'''

import os
import os.path

import shutil
import subprocess
import tempfile


class MatlabCallError(Exception):
    '''
    This error is raised when an error occurs during a subprocess call to Matlab.
    '''
    pass


class OctaveCallError(Exception):
    '''
    This error is raised when an error occurs during a subprocess call to Octave.
    '''
    pass


class SubprocessCallError(Exception):
    '''
    This error is raised when an error occurs during a subprocess call.
    '''
    pass


def matlab_solve(matfile_target, output_target, discard_matfile=True):
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
    run_command = "matlab -r \"SDPT3solve('{0}')\" -nodisplay -nojvm".format(
        matfile_target)
    try:
        msg = run_command_get_output(run_command, output_target)
    except SubprocessCallError, e:
        raise MatlabCallError(e)

    # Cleanup
    if discard_matfile:
        print "now deleting {0}".format(matfile_target)
        os.remove(matfile_target)

    return msg


def octave_solve(matfile_target, output_target, discard_matfile=True, cmd="octave"):
    '''
    The .mat is loaded into octave and the problem is solved with SDPT3.
    Inputs:
      matfile_target: the path to the .mat file containing the Sedumi format problem data.
      output_target: the path we will save the output log message to.
      discard_matfile: if True, deletes the .mat file after the solve finishes.
      cmd: command name for octave, which will be used for alternative command.
    Output:
        A dictionary with solve result information.
    '''
    # Generating the .mat file
    with tempfile.NamedTemporaryFile(
            suffix=".m", dir=os.path.dirname(matfile_target)) as runner:

        with open("SDPT3solve.m") as lib:
            shutil.copyfileobj(lib, runner)

        runner.write("SDPT3solve('{0}');\n".format(
            os.path.relpath(matfile_target)))
        runner.flush()

        run_command = "{cmd} {script}".format(
            cmd=cmd, script=os.path.relpath(runner.name))
        try:
            msg = run_command_get_output(run_command, output_target)
        except SubprocessCallError, e:
            raise OctaveCallError(e)

    # Cleanup
    if discard_matfile:
        print "now deleting {0}".format(matfile_target)
        os.remove(matfile_target)

    return msg


def run_command_get_output(run_command, output_target):
    '''
    Runs the command run_command, saves the output to output_target, and
    returns the output log.
    '''
    try:
        with open(output_target, "w") as fp:
            proc = subprocess.Popen(run_command, shell=True, stdout=fp)
            proc.communicate()

    except:
        err_msg = ("Something went wrong with the command. The command "
                   "run was:\n{0}\nPlease check that the command looks good "
                   "and that the the folder containing SDPT3solve.m is in the "
                   "Matlab or Octave path variable.").format(run_command)
        raise SubprocessCallError(err_msg)

    # Reading the log and returning its contents
    with open(output_target, 'r') as myfile:
        msg = myfile.read()

    return msg
