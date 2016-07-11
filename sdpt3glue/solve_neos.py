"""
Basic scraper/webdriver to submit an sdpt3 problem on the NEOS webpage.
This version uses selenium because difficulties were encountered using XML-RPC
for problems of this type.
"""

import os
import sys
import contextlib
from time import sleep
import xmlrpclib
from xmlrpclib import Fault
from xmlrpclib import ProtocolError
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


WEBDRIVERS = {
    "Firefox": webdriver.Firefox,
    "PhantomJS": webdriver.PhantomJS
}
""" Webdrivers to try using. """


def _print_fault(err, space=2):
    """ Print message from xmlrpclib.Fault.

    Args:
      err: xmlrpclib.Fault error.
      space: Space size to be added before each message.
    """
    print " " * space + "A fault occurred"
    print " " * space + "Fault code: {0}".format(err.faultCode)
    print " " * space + "Fault string: {0}".format(err.faultString)


def _print_protocol_error(err, space=2):
    """ Print message from xmlrpclib.ProtocolError.

    Args:
      err: xmlrpclib.ProtocolError error.
      space: Space size to be added before each message.
    """
    print " " * space + "A protocol error occurred"
    print " " * space + "URL: {0}".format(err.url)
    print " " * space + "HTTP/HTTPS headers: {0}".format(err.headers)
    print " " * space + "Error code: {0}".format(err.errcode)
    print " " * space + "Error message: {0}".format(err.errmsg)


@contextlib.contextmanager
def _get_driver():
    """ Try to make a webdriver according to installed browsers.

    Returns:
      Installed webdriver.

    Raises:
      RuntimeError: When no supported browsers are available.
    """
    for name, driver in WEBDRIVERS.items():
        try:
            res = driver()

        except (StandardError, WebDriverException) as e:
            sys.stderr.write(
                "{0} seems to be not installed: {1}\n".format(name, e))

        else:
            try:
                yield res
            finally:
                res.close()
                res.quit()
            return

    raise WebDriverException("No web drivers are available.")


class NeosError(Exception):
    """ Error caused by Neos server.

    This error is raised when an error occurs during calling Neos.
    """
    pass


def neos_solve(
        matfile_target, discard_matfile=True, no_prompt=False):
    '''
    Submits the Sedumi format .mat file to be solved on NEOS with SDPT3.
    Returns the solve result message from NEOS.
    If write_output_to, has the side effect of writing the message to this file.

    If no_prompt is True, it doesn't ask id and password manually and raise
    NeosError when some errors occur during connection to neos server.

    Raises:
      NeosError: When an error occurs by using Neos server.
    '''
    if not os.path.exists(matfile_target):
        raise ValueError(
            "The matfile {0} doesn't exist".format(matfile_target))

    # any backslashes need to be doubly escaped for the web form
    matfile_target = matfile_target.replace('\\', '\\\\')

    try:
        with _get_driver() as browser:
            browser.get(
                'http://www.neos-server.org/neos/solvers/sdp:sdpt3/MATLAB_BINARY.html')

            # Find the .mat upload box and input the path to ours
            file_upload_element = browser.find_element_by_name("field.2")
            file_upload_element.send_keys(matfile_target)
            assert file_upload_element.get_attribute('value'), \
                "Couldn't input file name, are you sure it exists?"

            # Find the submit button and click it
            submit_xpath = '//input[@type="submit"]'
            submit_button = browser.find_element_by_xpath(submit_xpath)
            submit_button.click()

            # After a few moments, the id and password will appear, and
            # we'll try to grab them automatically.
            source = browser.page_source
            jobid, pwd = extract_id_pwd(source)

    except WebDriverException as e:
        if no_prompt:
            raise NeosError(e)

        # If that fails for any reason, we ask the user to submit the problem
        # manually and copy-paste the lines giving the id and password.
        try:
            jobid, pwd = ask_user_to_submit(matfile_target)

        except EOFError as e:
            raise NeosError(e)

    neos_int = NeosInterface()
    msg = neos_int.track_and_return(jobid, pwd)

    # Cleanup
    if discard_matfile:
        os.remove(matfile_target)

    return msg


def extract_id_pwd(source):
    '''
    Given a snippet of the form

    .. code-block:: none

        Job#     : xxxxxxx
        Password : yyyyyyyy

    extracts and returns the strings for job ID and password

    '''
    start = source.find('Job#')
    snippet = source[start:start + 60]
    lines = snippet.split('\n')

    jobid_line = lines[0].strip().split()
    pwd_line = lines[1].strip().split()

    jobid = int(jobid_line[-1])
    pwd = pwd_line[-1]
    return jobid, pwd


def ask_user_to_submit(matfilepath):
    '''
    Instructs the user to manually submit their problem and then feed the ID
    and password back into the program.

    Raises:
      EOFError: When a user sends EOF.
    '''
    print (
        "Selenium submission failed, submit it manually!"
        "Find this files and submit them on the website:"
        "{0}"
        "Once you've submitted your problem, copy and paste the"
        "two lines that look like this"
        "        Job#     : xxxxxxx"
        "        Password : yyyyyyyy"
        "below and hit Enter. Or, you can just enter the job and"
        "password strings on consecutive lines.  Good luck!"
    ).format(matfilepath)

    user_input = ''
    while True:

        while not user_input:
            user_input = raw_input()

        try:
            jobid = int(user_input.strip().split()[-1])
            pwd = raw_input().strip().split()[-1]
            print "\n=============\n"
            return jobid, pwd

        except IndexError:
            print "\nTry again!\n"


class NeosInterface(object):
    """
    An abstract class for connections with the remote NEOS Server for
    Optimization. NeosInterface objects communicate with the NEOS Server via
    XML-RPC. This class wraps the server's services into a few convenient
    methods which, for the time being, are designed with the solution of AMPL
    models in mind.
    """

    def __init__(self, neos_host=None, neos_port=None):
         # Go to xmlrpc and flip on __verbose if you are debugging
         # and want to see ALL xml-rpc communication
        if not neos_host:
            neos_host = "neos.mcs.anl.gov"
        if not neos_port:
            neos_port = 3332

        neos_url = "http://{host}:{port}".format(
            host=neos_host, port=neos_port)
        self.server = xmlrpclib.ServerProxy(neos_url)

    def track_and_return(self, jobid, pwd):
        '''
        Takes a jobid and password for a solve already in progress,
        waits for its status to change to 'Done', and returns the message,
        jobid, and password.
        '''
        k = 20
        while True:

            try:
                status = self.server.getJobStatus(jobid, pwd)

            except Fault as err:
                _print_fault(err)
                print "  Error checking status: {0}  (will try again)".format(
                    sys.exc_info()[0])

            except ProtocolError as err:
                _print_protocol_error(err)
                print "  Error checking status: {0}  (will try again)".format(
                    sys.exc_info()[0])

            else:
                if status == "Done":
                    break

            sleep(k)

        msg = self.get_final_results(jobid, pwd).data
        return msg

    def get_final_results(self, jobid, pwd):
        '''
        This funtion is 'stubborn', meaning that if it's unable to get the
        results it will wait a few seconds and try again.  Stubborn
        functionality is intended to smooth over lost internet connections or
        computers that may fall asleep and then wake up and resume running
        code.
        '''
        while True:
            try:
                return self.server.getFinalResults(jobid, pwd)
            except Fault as err:
                _print_fault(err)
            except ProtocolError as err:
                _print_protocol_error(err)

            sleep(3)
