# -*- coding: utf-8 -*-
"""
Created on Thu Mar 27 16:43:25 2014

@author: Trish


Functions which express problems in Sedumi format and export them as .mat files
for Matlab
"""

from numpy import zeros, eye
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

    A, b, c, K = make_sedumi_format_problem(problem_data)
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

    c_star = zeros((1, num_sedumi_vars))
    c_star[0:nx] = 1.*problem_data['c']

    A_star = zeros((ne + ni + num_sdp_vars, num_sedumi_vars))
    b_star = zeros((ne + ni + num_sdp_vars, 1))

    A_star[0:ne, 0:nx] = 1.*problem_data['A']
    b_star[0:ne] = 1.*problem_data['b']

    A_star[ne:ne + ni, 0:nx] = 1.*problem_data['G'][:ni, :] # = Gl
    A_star[ne:ne + ni, nx:nx + ni] = eye(ni)
    b_star[ne:ne + ni] = 1.*problem_data['h'][:ni, :] # = hl

    A_star = zeros((num_sdp_vars, num_sedumi_vars))
    A_star[ne + ni:, 0:nx] = 1.*problem_data['G'][ni:, :] # = Gs
    A_star[ne + ni:, nx+ni:] = eye(num_sdp_vars)
    b_star[ne + ni:] = 1.*problem_data['h'][ni:, :] # = hs

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
    rows_to_keep = []
    cols_to_keep = []
    # Given var_i which is a free variable, figure out if there is a row k of
    # G_star such that Gs_star[ctr_k, var_i] == -1 AND hs[ctr_k] == 0 AND the
    # only other non-zero element in the row is Gs_star[ctr_k, nx + ni + ctr_k] == 1
    for var_i in range(nx):
        for ctr_k in range(ne + ni, ne + ni + num_sdp_vars):
            if equivalent_vars(A_star[ctr_k, :], b_star[ctr_k], var_i, nx + ni + ctr_k):
                A_star[:, nx+ni+ctr_k] += A_star[:, var_i]
                A_star[:, var_i] *= 0.
                c_star[nx+ni+ctr_k] += c_star[var_i]
                c_star[var_i] *= 0.
            else:
                rows_to_keep += [ctr_k]
                cols_to_keep += [var_i]
    rows_to_keep = range(ne + ni) + rows_to_keep
    cols_to_keep = cols_to_keep + range(nx, num_sedumi_vars)

#==============================================================================
#    SIMPLIFICATION STEP PART TWO: construct final matrices with only the rows/cols we want
#==============================================================================
    # new downsized problem
    A_star = A_star[rows_to_keep, cols_to_keep]
    b_star = b_star[rows_to_keep]
    c_star = c_star[cols_to_keep]

    # problem dimensions
    num_deleted_vars = (num_sedumi_vars - len(cols_to_keep))
    K = {'f': nx - num_deleted_vars, 'l': dims['l'], 's': dims['s']}
    return A_star, b_star, c_star, K




def equivalent_vars(g, h, i, j):
    '''
    Tests if the given constraint gx = h is in fact equivalent to the constraint
    x_i = x_j
    '''
    if g[i] != -g[j] or h != 0:
        return False
    else:
        g = 1.*g
        g[i] = 0
        g[j] = 0
        if sum(abs(g)) > 0:
            return False
    return True


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

