# -*- coding: utf-8 -*-
"""
Created on Thu Oct 01 01:29:40 2015

@author: Trish
"""

import re
from numpy import zeros


def make_result_dict(msg):
    assert can_use_msg(msg), "Stopping, the message is not properly formed."
    result_dict = extract_prop_dict(msg)
    result_dict['X'] = extract_X(msg)
    result_dict['status_verb'] =  get_verb_status(result_dict['status_num'])
    return result_dict



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
    
    for key in keylist:
        result_dict[keylist[key]] = None
    
    line_pattern = re.compile('\w[ \w:=.()]*[ \<\>]*=[ <>]*[ \d\.\-+e]*[\d\.\-+e]')
    phrase_pattern = re.compile('[\w\d\.\-+()][ \w\d\.\-+()]*')
    
    line_list = line_pattern.findall(msg)
    for line in line_list:
        line_parts = phrase_pattern.findall(line)
        key = line_parts[0].rstrip().replace("dual  ", "dual")
        val = handle_msg_item(line_parts[-1].strip())
        
        if key in keylist:
            if keylist[key] is not None:
                result_dict[keylist[key]] = val
    return result_dict



def extract_X(msg):
    '''
    Given the output message from running SDPT3solve.m, reconstruct the X
    matrix from the printed output and return it.
    '''
    
    if can_use_msg(msg):
        Xstart = msg.find('X{2} =') + 6
        Xend = msg.find('>>', Xstart)
        Xmsg = msg[Xstart:Xend]
        chunks = iter(Xmsg.split('\n\n'))
        X = None
        start, end = None, None
        try:
            while True:
                curr_chunk = chunks.next().strip()
                if curr_chunk[:7] == 'Columns':
                    curr_line = curr_chunk.split(' ')
                    start = int(curr_line[1])-1
                    end = int(curr_line[3])-1
                elif curr_chunk[:6] == 'Column':
                    curr_line = curr_chunk.split(' ')
                    start = int(curr_line[1])-1
                    end = start
                else:
                    lines = curr_chunk.split('\n')
                    if X is None:
                        size = len(lines)
                        X = zeros((size, size))
                        if start is None:
                            start = 0
                            end = size-1
#                        print "X created as a {0} by {0} matrix.".format(size)
                    for row, line in enumerate(lines):
                        line = re.sub('[\s][\s]*', ' ', line.strip()).split()
                        if len(line) != 0:
#                            print start, end, line
                            for col in range(start, end+1):
                                k = col - start
                                X[row, col] = float(line[k])
        except StopIteration:
            if X is not None:
                return X
    
    raise Exception("Something went wrong while extracting X from the message")



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
                x = int(x)
            return x
        except:
            pass
    return x



def get_verb_status(status_num):
    '''
    A function that takes an SDPT3 numerical termination code as input and
    returns a phrase (string) explaining the implications of the termination
    code.
    '''
    
    SDPT3_pos_status_map_verb = ['max(relative gap,infeasibility) < gaptol (OPTIMAL)',
                                 'primal problem is suspected to be infeasible',
                                 'dual problem is suspected to be infeasible',
                                 'norm(X) or norm(Z) diverging']
    SDPT3_neg_status_map_verb = ['max(relative gap,infeasibility) < gaptol (OPTIMAL)',
                                 'relative gap < infeasibility',
                                 'lack of progress in predictor or corrector',
                                 'X or Z not positive definite',
                                 'difficulty in computing predictor or corrector direction',
                                 'progress in relative gap or infeasibility is bad',
                                 'maximum number of iterations reached',
                                 'primal infeasibility has deteriorated too much',
                                 'progress in relative gap has deteriorated',
                                 'lack of progress in infeasibility']

    if status_num is None:
        return "no termination code given"
    elif status_num >= 0:
        return SDPT3_pos_status_map_verb[status_num]
    else:
        return SDPT3_neg_status_map_verb[-status_num]


def make_result_summary(result_dict):
    '''
    Prints a basic summary of information about an SDPT3 solve result.
    '''
    
    return """SDPT3 solve finished with status code {0['solverstatus']}: {0['verb_status']}
Primal value (from X): {0['primal_z']} (infeasibility: {0['rel_primal_feas']})
Dual value (bound): {0['dual_z']} (infeasibility: {0['rel_dual_feas']})
Relative gap: {0['rel_gap']}
Solve time: {1} s
""".format(result_dict, 0.001*round(1000*result_dict['solve_time']))