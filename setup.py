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
    version='0.9.1',
    description=(
        'Glue code for solving semidefinite programs '
        'in Cvxpy format using the SDPT3 package for Matlab.'
    ),
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
