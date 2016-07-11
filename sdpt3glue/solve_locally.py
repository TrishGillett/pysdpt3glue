'''
Methods that run code on a copy of Matlab or Octave installed on the user's
machine.
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


def matlab_solve(matfile_target, discard_matfile=True):
    '''
    The .mat is loaded into matlab and the problem is solved with SDPT3.

    Args:
        matfile_target: the path to the .mat file containing the Sedumi format problem data.
        discard_matfile: if True, deletes the .mat file after the solve finishes.

    Returns:
        A dictionary with solve result information.
    '''
    # Generating the .mat file
    run_command = "matlab -r \"SDPT3solve('{0}')\" -nodisplay -nojvm".format(
        matfile_target)
    try:
        msg = run_command_get_output(run_command)
    except SubprocessCallError, e:
        raise MatlabCallError(e)

    # Cleanup
    if discard_matfile:
        print "now deleting {0}".format(matfile_target)
        os.remove(matfile_target)

    return msg


def octave_solve(matfile_target, discard_matfile=True, cmd="octave"):
    '''
    The .mat is loaded into octave and the problem is solved with SDPT3.

    Args:
        matfile_target: the path to the .mat file containing the Sedumi format problem data.
        discard_matfile: if True, deletes the .mat file after the solve finishes.
        cmd: command name for octave, which will be used for alternative command.

    Returns:
        A dictionary with solve result information.
    '''
    # Generating the .mat file
    with tempfile.NamedTemporaryFile(
        suffix=".m", dir=os.path.dirname(matfile_target)) as runner:

        with open(os.path.join(os.path.dirname(__file__), "SDPT3solve.m")) as lib:
            shutil.copyfileobj(lib, runner)

        runner.write("SDPT3solve('{0}');\n".format(
            os.path.relpath(matfile_target)))
        runner.flush()

        run_command = "{cmd} {script}".format(
            cmd=cmd, script=os.path.relpath(runner.name))
        try:
            msg = run_command_get_output(run_command)
        except SubprocessCallError, e:
            raise OctaveCallError(e)

    # Cleanup
    if discard_matfile:
        print "now deleting {0}".format(matfile_target)
        os.remove(matfile_target)

    return msg


def run_command_get_output(run_command):
    '''
    Runs the command run_command, saves the output to output_target, and
    returns the output log.
    '''
    # Performing the Matlab solve
    try:
        proc = subprocess.Popen(
            run_command, shell=True, stdout=subprocess.PIPE,
            cwd=os.path.join(os.path.dirname(__file__)))
        return proc.communicate()[0]

    except:
        err_msg = ("Something went wrong with the command. The command "
                   "run was:\n{0}\nPlease check that the command looks good "
                   "and that the the folder containing SDPT3solve.m is in the "
                   "Matlab or Octave path variable.").format(run_command)
        raise SubprocessCallError(err_msg)
