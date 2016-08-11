Quick guide: Four ways to use sdpt3glue
=======================================

Given an SDP problem P formulated in Cvxpy, the following methods are
accommodated.

1. With Matlab installed
''''''''''''''''''''''''

Make sure SDPT3 is installed for Matlab and the folder containing SDPT3 is
added to your MATLABPATH.  Solve the problem by executing the following
command:

.. code-block:: python

   result = sdpt3glue.sdpt3_solve_problem(P, sdpt3glue.MATLAB, matfile_target,
                                          output_target=output_target)

where ``matfile_target`` is the filepath that the problem's .mat file will be
saved to and ``output_target`` is the filepath that the SDPT3 solve log will
be saved to.

2. With Octave installed
''''''''''''''''''''''''

Make sure SDPT3 is installed for Octave and is visible in Octave when the
working folder is the folder where ``matfile_target`` is.

.. code-block:: python

   result = sdpt3glue.sdpt3_solve_problem(P, sdpt3glue.OCTAVE, matfile_target,
       output_target=output_target)

3. Using Docker
'''''''''''''''

Without a locally installed copy of Matlab or Octave, but with Docker, a
problem can be solved in the following way:

.. code-block:: python

   OCTAVE_CMD = (
       "docker run --rm -it -v {workdir}:/data "
       "jkawamoto/octave-sdpt3 octave"
   ).format(workdir=os.path.abspath("."))

   result = sdpt3glue.sdpt3_solve_problem(P, sdpt3glue.OCTAVE, matfile_target,
       output_target=output_target, cmd=OCTAVE_CMD)

This makes use of a docker image created by Junpei Kawamoto for this purpose.

4. With the NEOS server
'''''''''''''''''''''''

With either Firefox or phantomjs installed and for small to medium sized
problems (those with .mat files of size less than about 20-25MB), the NEOS
server can be used.  Disclaimer: In addition to the disclaimer provided by the
MIT license, we make special note that we make no guarantees about service
provided by the NEOS server, as we are not responsible for its operation.  If
your problem data is sensitive, take appropriate precautions.

.. code-block:: python

   result = sdpt3glue.sdpt3_solve_problem(P, sdpt3glue.NEOS, matfile_target,
       output_target=output_target)
