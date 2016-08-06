#
# setup.py
#
# Copyright (c) 2016 Trish Gillett-Kawamoto
#
# This software is released under the MIT License.
#
# http://opensource.org/licenses/mit-license.php
#
""" sdpt3glue package information.
"""
from setuptools import setup, find_packages


def _load_requires_from_file(filepath):
    """ Read a package list from a given file path.

    Args:
      filepath: file path of the package list.

    Returns:
      a list of package names.
    """
    with open(filepath) as fp:
        return [pkg_name.strip() for pkg_name in fp.readlines()]


setup(
    name='sdpt3glue',
    version='0.9.2',
    description=(
        'Glue code for solving semidefinite programs '
        'in Cvxpy format using the SDPT3 package for Matlab.'
    ),
      long_description="""The sdpt3glue package serves as glue code to allow semidefinite programming (SDP problems modeled using Cvxpy to be solved using the Matlab-compatible solver SDPT3.

SDPT3 can be used in a number of ways:

- on an installed copy of Matlab with SDPT3,

- on an installed copy of Octave with SDPT3,

- using a Docker image of Octave with SDPT3,

- by sending the problem to the NEOS server and retrieving the answer.""",
    author="Trish Gillett-Kawamoto",
    author_email="discardthree@gmail.com",
    url="https://github.com/discardthree/PySDPT3glue",
    packages=find_packages(exclude=["tests"]),
    package_data={'sdpt3glue': ['*.m']},
    install_requires=_load_requires_from_file("requirements.txt"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Mathematics"
    ],
    test_suite='tests.suite',
    license="MIT"
)
