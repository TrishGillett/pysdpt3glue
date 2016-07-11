"""

"""

import re
from numpy import zeros


_SDPT3_POS_STATUS_MAP_VERB = (
    'max(relative gap,infeasibility) < gaptol (OPTIMAL)',
    'primal problem is suspected to be infeasible',
    'dual problem is suspected to be infeasible',
    'norm(X) or norm(Z) diverging'
)

_SDPT3_NEG_STATYS_MAP_VERB = (
    'max(relative gap,infeasibility) < gaptol (OPTIMAL)',
    'relative gap < infeasibility',
    'lack of progress in predictor or corrector',
    'X or Z not positive definite',
    'difficulty in computing predictor or corrector direction',
    'progress in relative gap or infeasibility is bad',
    'maximum number of iterations reached',
    'primal infeasibility has deteriorated too much',
    'progress in relative gap has deteriorated',
    'lack of progress in infeasibility'
)


def make_result_dict(msg):
    '''
    Extracts some solve information from the log message and constructs a dict.
    This function will error if the message is empty or does not include the phrase
    "SDPT3: Infeasible path-following algorithms", which is an indicator that the
    solver at least started okay.  If the log passes that basic test, we just retrieve
    what information we can.  If the dict doesn't at least contain a status_num and
    status_verb, you should check the log manually and see what went wrong.
    '''
    assert can_use_msg(
        msg), "Stopping, the message is not properly formed: " + msg
    result_dict = extract_prop_dict(msg)
    result_dict['Xvars'] = extract_X(msg)
    result_dict['status_verb'] = get_verb_status(result_dict['status_num'])
    return result_dict


def make_result_summary(result):
    '''
    Prints a basic summary of information about an SDPT3 solve result.
    '''
    return (
        "SDPT3 solve finished with status code {0[status_num]}: {0[status_verb]}"
        "Primal value (from X): {0[primal_z]} (infeasibility: {0[rel_primal_feas]})"
        "Dual value (bound): {0[dual_z]} (infeasibility: {0[rel_dual_feas]})"
        "Relative gap: {0[rel_gap]}"
        "Solve time: {1} s"
    ).format(result, 0.001 * round(1000 * result['solve_time']))


def print_summary(result):
    ''' Prints out the summary produced by make_result_summary. '''
    print "\nResult summary:\n" + make_result_summary(result)


def can_use_msg(msg):
    '''
    Checks to see if a message is non-trivial and contains the phrase
    "SDPT3: Infeasible path-following algorithms", which should appear in the
    output log just before the result properties are listed.  While it's
    probably possible for this function to return True in a case where there's
    something wrong with the message, this is a good preliminary check to do.
    '''
    return msg is not None and "SDPT3: Infeasible path-following algorithms" in msg


def extract_prop_dict(msg):
    '''
    Given the output message from running SDPT3solve.m, this function
    constructs and returns a dictionary of basic solve result information.
    '''
    result_dict = {}

    # the key is what we look for in the SDPT3 message output, the value is
    # the name of key we'll save the information to in the output dict.
    keylist = {'number of iterations': 'iterations',
               'primal objective value': 'primal_z',
               'dual objective value': 'dual_z',
               'gap': 'abs_gap',
               'relative gap': 'rel_gap',
               'actual relative gap': 'actual_rel_gap',
               'rel. primal infeas': 'rel_primal_feas',
               'rel. dual infeas': 'rel_dual_feas',
               'Total CPU time (secs)': 'solve_time',
               'CPU time per iteration': 'solve_time_per_iter',
               'termination code': 'status_num'}

    for key in keylist.values():
        result_dict[key] = None

    line_pattern = re.compile(
        r'\w[ \w:=.()]*[ \<\>]*=[ <>]*[ \d\.\-+e]*[\d\.\-+e]')
    phrase_pattern = re.compile(r'[\w\d\.\-+()][ \w\d\.\-+()]*')

    line_list = line_pattern.findall(msg)
    for line in line_list:
        line_parts = phrase_pattern.findall(line)
        key = line_parts[0].rstrip().replace("dual  ", "dual")
        val = handle_msg_item(line_parts[-1].strip())

        if key in keylist and keylist[key] is not None:
            result_dict[keylist[key]] = val
    return result_dict


def extract_X(msg):
    '''
    Given the output message from running SDPT3solve.m, reconstruct the X
    matrix from the printed output and return it.
    '''
    # First pull out the definitions.  Each starts with 'X{numbers} ='
    # and we'll keep grabbing text until we hit any of the characters >, <, *,
    # or X
    var_pattern = re.compile(r'X\{[\d]*\} =[^><\*X]*')
    var_list = var_pattern.findall(msg)

    # Xlist will hold the solution variables or matrices
    Xlist = [None] * len(var_list)

    for i, Xmsg in enumerate(var_list):
        # Drop the "X{something} =" and strip extra whitespace
        Xstart = Xmsg.find('=') + 1
        Xmsg = Xmsg[Xstart:].strip()

        # From Xmsg we can judge if the current variable is a matrix displaying in chunks
        # due to display width constraints, a matrix displaying all in one chunk,
        # or a scalar.
        if 'Column' in Xmsg:
            # If X[i] is a chunked matrix, each chunk has a header containing 'Column'
            # Split the data into chunks
            chunk_pattern = re.compile('Column[^C]*')
            chunk_list = chunk_pattern.findall(Xmsg)

            # Use regular expressions to split the data into header parts and
            # data parts
            header = re.compile(r'Columns* [\d]+[ through [\d]+]?')
            header_list = header.findall(Xmsg)
            chunk_list = header.split(Xmsg)[1:]  # drop the first, which is ''
            assert len(header_list) == len(chunk_list)

            # Find out how many columns the matrix has by grabbing the last column number
            # from the last header
            int_pattern = re.compile(r'\d[\d]*')
            int_list = int_pattern.findall(header_list[-1])
            cols = int(int_list[-1])
            # We'll count rows and initialize the matrix during the processing of
            # the first chunk.

            # Take a matching header and chunk and place the chunk's data in
            # the columns of Xlist[i] which are indicated by the header.
            for header, chunk in zip(header_list, chunk_list):
                # Grab the column numbers from the header, note the first one. It's
                # the start column we'll use to place the chunk's data in the
                # matrix.
                int_list = [int(x) for x in int_pattern.findall(header)]
                col_start = int_list[0] - 1

                # Split the chunk into rows
                chunk = chunk.strip()
                chunk = re.sub(' *\n *', '\n', chunk)
                chunk_lines = chunk.split('\n')

                # Initialize the matrix now if it hasn't been done yet.
                if Xlist[i] is None:
                    rows = len(chunk_lines)
                    Xlist[i] = zeros((rows, cols))

                # Plug the row's data into the matrix
                for row, line in enumerate(chunk_lines):
                    for k, item in enumerate(re.split(r'\s+', line)):
                        Xlist[i][row, col_start + k] = float(item)
            print "Imported X[{0}] as a matrix with shape {1}.".format(i, Xlist[i].shape)

        elif ' ' in Xmsg or '\n' in Xmsg:
            # Otherwise if it has spaces or line breaks it's a non-chunked
            # matrix
            Xmsg = Xmsg.strip()
            Xmsg = re.sub(' +', ' ', Xmsg)
            Xmsg = re.sub(' *\n *', '\n', Xmsg)
            Xmsg_lines = Xmsg.split('\n')

            # Initialize the matrix.
            rows = len(Xmsg_lines)
            cols = len(Xmsg_lines[0].split())
            Xlist[i] = zeros((rows, cols))

            # Plug the row's data into the matrix
            for row, line in enumerate(Xmsg_lines):
                for k, item in enumerate(re.split(r'\s+', line.strip())):
                    Xlist[i][row, k] = float(item)
            print "Imported X[{0}] as a matrix with shape {1}.".format(i, Xlist[i].shape)

        else:
            # Otherwise it's a scalar
            Xlist[i] = float(Xmsg)
            print "Imported X[{0}] as a scalar.".format(i)

    return Xlist


def handle_msg_item(x):
    '''
    A function that takes a string x and returns it's interpretation as an int,
    float, or string in that order of preference.  If x is None, None is
    returned.
    '''
    if len(x) == 0:
        return None
    else:
        try:
            x = float(x)
            if int(x) == x:
                return int(x)
            else:
                return x
        except (TypeError, ValueError):
            pass
    return x


def get_verb_status(status_num):
    '''
    A function that takes an SDPT3 numerical termination code as input and
    returns a phrase (string) explaining the implications of the termination
    code.
    '''
    if status_num is None:
        return "no termination code given"
    elif status_num >= 0:
        return _SDPT3_POS_STATUS_MAP_VERB[status_num]
    else:
        return _SDPT3_NEG_STATYS_MAP_VERB[-status_num]
