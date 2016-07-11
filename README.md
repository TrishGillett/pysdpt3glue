# py-sdpt3-glue
[![Code Climate](https://codeclimate.com/github/discardthree/py-sdpt3-glue/badges/gpa.svg)](https://codeclimate.com/github/discardthree/py-sdpt3-glue)
[![Build Status](https://travis-ci.org/discardthree/PySDPT3glue.svg?branch=master)](https://travis-ci.org/discardthree/PySDPT3glue)
[![MIT License](http://img.shields.io/badge/license-MIT-blue.svg?style=flat)](LICENSE)

The sdpt3glue package serves as glue code to allow Cvxpy semidefinite programming (SDP) problems to be solved using the SDPT3 solver for Matlab.

##Installation:
This project is listed under PyPI as [sdpt3glue](https://pypi.python.org/pypi/sdpt3glue/), which means that you should be able to install it using
```
pip install sdpt3glue
```

##Quick usage guide: 

### Problem set up
We assume that the problem to be solved is a Cvxpy problem object representing a semidefinite program.  For example, to use sdpt3glue to solve the problem
```
    min y s.t.
    -0.2 <= x <= -0.1
    0.4 <= z <=  0.5
    [1  x  y]
    |x  1  z| is PSD
    [y  z  1]
```
the following script lays the ground work by modeling the problem with Cvxpy and defining the file targets for the .mat file and the output log:

```py
import os

from cvxpy import *
import sdpt3glue.solve as slv

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
```

###Problem solution four ways


**1. With Matlab installed**

Make sure SDPT3 is installed for Matlab and the folder containing SDPT3 is
added to your MATLABPATH.  Solve the problem by executing the following
command:

```py
result = sdpt3glue.sdpt3_solve_problem(P, sdpt3glue.MATLAB, matfile_target,
                                       output_target=output_target)
```

where ``matfile_target`` is the filepath that the problem's .mat file will be
saved to and ``output_target`` is the filepath that the SDPT3 solve log will
be saved to.

**2. With Octave installed**

Make sure SDPT3 is installed for Octave and is visible in Octave when the
working folder is the folder where ``matfile_target`` is.


```py
result = sdpt3glue.sdpt3_solve_problem(P, sdpt3glue.OCTAVE, matfile_target,
                                       output_target=output_target)
```

**3. Using Docker**

Without a locally installed copy of Matlab or Octave, but with Docker, a problem can be solved in the following way:

```py
OCTAVE_CMD = ("docker run --rm -it -v {workdir}:/data "
              "jkawamoto/octave-sdpt3 octave").format(workdir=os.path.abspath("."))

result = sdpt3glue.sdpt3_solve_problem(P, sdpt3glue.OCTAVE, matfile_target,
                                       output_target=output_target, cmd=OCTAVE_CMD)
```

This makes use of a docker image created by Junpei Kawamoto for this purpose.

**4. With the NEOS server**

With either Firefox or phantomjs installed and for small to medium sized problems (those with .mat files of size less than about 20-25MB), the NEOS server can be used.

Disclaimer: In addition to the disclaimer provided by the MIT license, we make special note that we make no guarantees about service provided by the NEOS server, as we are not responsible for its operation.  If your problem data is sensitive, take appropriate precautions.

```py
result = sdpt3glue.sdpt3_solve_problem(P, sdpt3glue.NEOS, matfile_target,
                                       output_target=output_target)
```
