# -*- coding: utf-8 -*-
"""
Created on Thu Mar 27 16:43:25 2014

@author: Trish


Functions which express problems in Sedumi format and export them as .mat files
for Matlab
"""

import numpy as np
import scipy.io



def write_sedumi_model(problem_data, target):
    '''
    Input:
        problem_data: As produced by applying get_problem_data['CVXOPT'] to a
        cvxpy problem.
    Returns: (None)
    Effect:
        Saves a .mat file containing the A, b, c, K that define the problem
        in Sedumi format (see http://plato.asu.edu/ftp/usrguide.pdf )
    '''

#    raise Warning("This is a max problem and Sedumi format handles min problems, "
#        "so the objective function has been negated and you will need to "
#        "negate the result of the solve to get back the actual opt val to the "
#        "relaxation.")

    A, b, c, K, offset = make_sedumi_format_problem(problem_data)
    assert offset == 0
    A = sparsify_tall_mat(A)
    b = sparsify_tall_mat(b)
    c = sparsify_tall_mat(c)
    scipy.io.savemat(target, {'A': A, 'b': b, 'c': c, 'K': K})
    return target



def make_sedumi_format_problem(problem_data):
    '''
    Input:
        problem_data: As produced by applying get_problem_data['CVXOPT'] to a
        cvxpy problem.
    Returns:
        A, b, c, K: Data defining an equivalent problem in Sedumi format.
    '''
    dims = problem_data['dims']
    assert not dims['q'], "Sorry, at this time we can't handle SOC constraints!"

    nx = len(problem_data['c'])
    ni = dims['l']
    ne = len(problem_data['b'])
    num_sdp_vars = sum([s*s for s in dims['s']])

#==============================================================================
#   EXPANSION STEP:
#   Construct the expanded vector c_star and matrices A_star and Gs_star
#
#   At this point...
#     c_star = [ c ] (nx)
#              [ 0 ] (ni + num_sdp_vars)
#
#     A_star = [ A  |  0  |  0 ] (ne)        => eqs written in new vars
#              [ Gl |  I  |  0 ] (ni)        => ineqs written as eqs in new vars
#     Gs_star= [ Gs |  0  |  I ] (num_sdp_vars) => sets the exp in the SDP element
#               (nx) (ni)(num_sdp_vars)          equal to the var representing it
#==============================================================================
    num_sedumi_vars = nx + ni + num_sdp_vars

    c_star = np.zeros((1, num_sedumi_vars))
    c_star[0:nx] = 1.*problem_data['c']

    A_star = np.zeros((ne + ni + num_sdp_vars, num_sedumi_vars))
    b_star = np.zeros((ne + ni + num_sdp_vars, 1))

    A_star[0:ne, 0:nx] = 1.*problem_data['A']
    b_star[0:ne] = 1.*problem_data['b']

    A_star[ne:ne + ni, 0:nx] = 1.*problem_data['G'][:ni, :] # = Gl
    A_star[ne:ne + ni, nx:nx + ni] = np.eye(ni)
    b_star[ne:ne + ni] = 1.*problem_data['h'][:ni, :] # = hl

    A_star = np.zeros((num_sdp_vars, num_sedumi_vars))
    A_star[ne + ni:, 0:nx] = 1.*problem_data['G'][ni:, :] # = Gs
    A_star[ne + ni:, nx+ni:] = np.eye(num_sdp_vars)
    b_star[ne + ni:] = 1.*problem_data['h'][ni:, :] # = hs

    K = {'f': nx, 'l': dims['l'], 's': dims['s']}
    A_star, b_star, c_star, K, obj_cst = simplify_sedumi_model(A_star,
                                                               b_star,
                                                               c_star,
                                                               K,
                                                               allow_nonzero_b=False)
    assert obj_cst == 0, "This shouldn't be possible with allow_nonzero_b=False."
    return simplify_sedumi_model(A_star, b_star, c_star, K)


def simplify_sedumi_model(A, b, c, K, allow_nonzero_b=False):
    '''
    Tries to eliminate variables using a few simple strategies:
        1. If a constraint is expressing Akixi = bk where variable xi is
           a free variable, we can eliminate x.
        2. If a constraint is expressing Akixi + Akjxj = bk where variable xi
           is a free variable, we can eliminate x.
    Input:    A, b, c, K: for a problem in Sedumi format
              allow_nonzero_b: If False, only eliminate if bk = 0 is zero
    Returns:  A, b, c, K: for the simplified problem.
              offset: A constant which must be added to the optimal value of
              the simplified problem in order to make it equivalent.  With
              allow_nonzero_b, offset will be 0.
    '''
    n_free = K['f'] # the first n_elig variables will be eligible for elimination
    n_vars = c.size
    n_ctr = b.size

#==============================================================================
#   SIMPLICATION STEP:
#   If some ctr k of A_star*x = hs is actually just equating xi = xj
#   for some i in the free vars, j in the sdp vars, we need to do the following:
#     (1) for A_star, c, add column/element i to column/element j
#     (2) for A_star, c, delete column/element i
#     (3) for A_star, delete row k
#     (4) adjust our counts for different variable/constraint types
#   On the first pass we will do (1) and make lists of which rows/ctrs to eliminate.
#   On a second pass we will do the rest.
#
#   SIMPLIFICATION PART ONE: Remove dependence on some cols and mark them for removal.
#==============================================================================
    rows_to_keep = []            # construct this additively
    cols_to_keep = range(n_vars) # construct this subtractively
    n_deleted_f = 0
    n_deleted_l = 0
    offset = 0
    # Given var_i which is a free variable, figure out if there is a row k of
    # G_star such that Gs_star[ctr_k, var_i] == -1 AND hs[ctr_k] == 0 AND the
    # only other non-zero element in the row is Gs_star[ctr_k, nx + ni + ctr_k] == 1
    for ctr_k in range(n_ctr):
        i, j = check_eliminatibility(A[ctr_k, :], b[ctr_k, 0], n_elig=n_free, allow_nonzero_b=allow_nonzero_b)
        if i is not None and c[0, i] != 0 and b[ctr_k, 0]:
            # This case involves shifting the objective by a constant and we
            # need to decide how to handle that, so for now just not doing anything.
            rows_to_keep += [ctr_k]
        elif i is not None:
            # Akixi (optionally + Akjxj) = bk case, eliminate xi using xi = (Akj/Aki) - (bk/Aki)*x_j
            aki = A[ctr_k, i]
            bk = b[ctr_k, 0]
            factor = 1.*bk/aki
            b[:, 0] += -factor*A[:, i]
            offset += -factor*c[0, i]

            if j is not None:
                # Akixi + Akjxj = bk case
                akj = A[ctr_k, j]
                factor = 1.*akj/aki
                A[:, j] += -factor*A[:, i]
                c[0, j] += -factor*c[0, i]

            # zero out the coefficients of var i to make sure it isn't chosen for elimination again
            A[:, i] *= 0.
            c[0, i] *= 0.
            cols_to_keep.remove(i)
            n_deleted_f += 1
        else:
            rows_to_keep += [ctr_k]

    # As a final step, see if there are any free or nonnegative variables that
    # aren't involved in ctrs or the objective
    index = 0
    while index < len(cols_to_keep):
        vars_fl = n_free + K['l']
        col = cols_to_keep[index]
        # free vars not in constraints must have 0 coeff in obj, else unbounded.
        # nonneg vars not in constraints must have >=0 coeff in obj, else unbounded.
        # if a var makes the probblem unbounded, we'll leave it alone and let
        # the user find out when they actually solve.
        free_and_deletable = col < n_free and c[0, col] == 0
        nneg_and_deletable = col >= n_free and col < vars_fl and c[0, col] >= 0
        if free_and_deletable and not abs(A[:, col]).any():
            cols_to_keep.pop(index)
            n_deleted_f += 1
        elif nneg_and_deletable and not abs(A[:, col]).any():
            cols_to_keep.pop(index)
            n_deleted_l += 1
        else:
            index += 1

    # or any ctrs that are trivial (0x = 0).  A ctr of 0x = b would make the
    # problem infeasible, but in that case we'll leave it in so the user finds
    # it when they solve.
    index = 0
    while index < len(rows_to_keep):
        row = rows_to_keep[index]
        if not abs(A[row, :]).any() and b[row, 0] == 0:
            rows_to_keep.pop(index)
        else:
            index += 1

#==============================================================================
#    SIMPLIFICATION STEP PART TWO: construct final matrices with only the rows/cols we want
#==============================================================================
    # new downsized problem
    A = A[np.ix_(rows_to_keep, cols_to_keep)]
    b = b[np.ix_(rows_to_keep, [0])]
    c = c[np.ix_([0], cols_to_keep)]

    # problem dimensions
    assert len(cols_to_keep) + n_deleted_f + n_deleted_l
    K = {'f': K['f'] - n_deleted_f, 'l': K['l'] - n_deleted_l, 's': K['s']}
    return A, b, c, K, offset



def check_eliminatibility(g, h, n_elig=None, allow_nonzero_b=False):
    '''
    Tests if constraint gx = h fits one of the patterns:
       1. ax_i = d
       2. ax_i + bx_j = d
    with the requirement that the x_i variable be one of the first n_elig variables.
    Returns:
        i, None      if the constraint fits pattern 1
        i, j         if the constraint fits pattern 2
        None, None   otherwise
    '''
    n = g.shape[1]

    if n_elig is None:
        n_elig = n

    if not allow_nonzero_b and h != 0:
        return None, None

    for i in range(n_elig):
        if g[0, i] != 0:
            j = i+1
            while j < n and g[0, j] == 0:
                j += 1
            # having stopped, see which we have found:
            if j == n:
                return i, None # the end of the row
            elif not abs(g[0, j+1:]).any():
                return i, j # the second of exactly two nonzero coefficients
            else:
                return None, None # the second of three or more nonzero coefficients

    # If nothing's been returned yet, it's because all the eliminatible vars' coeffs are zero.
    return None, None


def sparsify_tall_mat(M, block_height=1000):
    '''
    Returns a sparse matrix in scipy.sparse.coo_matrix form which is equivalent to M
    '''
    i = 0
    spmat_collector = []
    while i*block_height < M.shape[0]:
        curr_block = M[i*block_height:(i+1)*block_height, :]
        spmat_collector += [scipy.sparse.coo_matrix(curr_block.astype('d'))]
        i += 1
    return scipy.sparse.construct.vstack(spmat_collector)

