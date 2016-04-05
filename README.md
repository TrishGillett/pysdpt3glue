# py-sdpt3-glue
<a href="https://codeclimate.com/github/discardthree/py-sdpt3-glue"><img src="https://codeclimate.com/github/discardthree/py-sdpt3-glue/badges/gpa.svg" /></a>

Glue code for solving Cvxpy SDP problems using Matlab's SDPT3.
This package is for you if:
- You have a semidefinite program constructed as a Cvxpy problem
- Your problem has only one semidefinite constraint (extension to general case coming soon)
- You want to solve it using SDPT3
- You want to do the solves on your own computer and
  - You have Matlab installed locally
  - SDPT3 is installed
  - You have added the folder containing SDPT3 to your MATLABPATH
- or you want to use SDPT3 on the wonderful NEOS server and
  - You have firefox installed
  - Your .mat's file size isn't over NEOS' file size limit)
