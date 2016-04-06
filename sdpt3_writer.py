# -*- coding: utf-8 -*-
"""
Created on Thu Mar 27 16:43:25 2014

@author: Trish


Functions which generate .mat files for SDPT3 solves
"""

from numpy import zeros, eye
import scipy.io


def makeSDPT3Model(P_data, target, verbose=False):
    '''
    Save a .mat file containing the information for an SDPT3 solve in Sedumi
    format (see http://plato.asu.edu/ftp/usrguide.pdf )
    '''

    dims = P_data['dims']
    Gl = 1.*P_data['G'][:dims['l'], :]
    hl = 1.*P_data['h'][:dims['l'], :]
    Gs = 1.*P_data['G'][dims['l']:, :]
    hs = 1.*P_data['h'][dims['l']:, :]
    A = 1.*P_data['A']
    b = 1.*P_data['b']
    c = 1.*P_data['c']

    assert not dims['q'], "Sorry, at this time we can't handle SOC constraints!"
    nx = Gl.size[1]
    ne = A.size[0]
    ni = Gl.size[0]
    print "\nSDP model with {0}x{0} variable matrix, {1} total variables, {2} eq ctrs, {3} ineq ctrs".format(dims['s'][0], nx, ne, ni)

    if verbose:
        print "\nSDP to Sedumi format transformation:"
        print "{0} equality constraints in {1} variables".format(ne + ni, nx + ni)
        print "the first {0} variables (slacks) are in the nonnegative cone".format(ni)
        print "the remaining {0} variables form a matrix in the PSD cone".format(nx)

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
    num_sdp_vars = sum([s*s for s in dims['s']])
    num_sedumi_vars = nx + ni + num_sdp_vars
    
    c_star = zeros((1, num_sedumi_vars))
    c_star[0:nx] = c

    A_star = zeros((ne + ni, num_sedumi_vars))
    b_star = zeros((ne + ni, 1))

    A_star[0:ne, 0:nx] = A
    b_star[0:ne] = b

    A_star[ne:ne + ni, 0:nx] = Gl
    A_star[ne:ne + ni, nx:nx + ni] = eye(ni)
    b_star[ne:ne + ni] = hl

    assert Gs.size[0] == num_sdp_vars
    Gs_star = zeros((num_sdp_vars, num_sedumi_vars))
    Gs_star[0:num_sdp_vars, 0:nx] = Gs
    Gs_star[0:num_sdp_vars, nx+ni:] = eye(num_sdp_vars)

#==============================================================================
#   SIMPLICATION STEP:
#   If some ctr k of Gs_star*x = hs is actually just equating xi = xj
#   for some i in the free vars, j in the sdp vars, we need to do the following:
#     (1) for A_star, Gs_star, c, add column/element i to column/element j
#     (2) for A_star, Gs_star, c, delete column/element i
#     (3) for Gs_star, delete row k
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
        for ctr_k in range(num_sdp_vars):
            delete = False
            if Gs_star[ctr_k, var_i] == -1:
                assert Gs_star[ctr_k, nx + ni + ctr_k] == 1 # Should be true by construction
                ctr_copy = 1.*Gs_star[ctr_k, :]
                ctr_copy[0, var_i] = 0
                ctr_copy[0, nx+ni+ctr_k] = 0
                if hs[ctr_k] == 0 and sum(abs(ctr_copy)) == 0:
                    # We can eliminate var_i because it meets the criteria!
                    Gs_star[:, nx+ni+ctr_k] += Gs_star[:, var_i]
                    A_star[:, nx+ni+ctr_k] += A_star[:, var_i]
                    c_star[nx+ni+ctr_k] += c_star[var_i]
                    # We're going to delete this column, but let's zero it out to avoid confusion
                    Gs_star[:, var_i] *= 0.
                    A_star[:, var_i] *= 0.
                    c_star[var_i] *= 0.
                    # Make a note to delete the row and column that are now 0.
                    delete = True
            if not delete:
                rows_to_keep += [ctr_k]
                cols_to_keep += [var_i]
    cols_to_keep += range(nx, num_sedumi_vars)

#==============================================================================
#    SIMPLIFICATION STEP PART TWO: construct final matrices with only the rows/cols we want
#==============================================================================
    num_deleted_vars = (num_sedumi_vars - len(cols_to_keep))
    new_nx = nx - num_deleted_vars

    sedumi_A = zeros((ne + ni + rows_to_keep, new_nx + ni + num_sdp_vars))
    sedumi_b = zeros((ne + ni + rows_to_keep, 1))

    # linear eqs and ineqs from cvxopt problem
    sedumi_A[:ne + ni, :] = A_star[:, cols_to_keep]
    sedumi_b[:ne + ni, :] = b_star[:]

    # sum_i(s_i^2) rows for the semidefinite constraints
    sedumi_A[ne + ni:, :] = Gs_star[rows_to_keep, cols_to_keep]
    sedumi_b[ne + ni:, :] = hs[rows_to_keep, :]
    
    # objective and dimensions
    sedumi_c = c_star[cols_to_keep]
    sedumi_K = {'f': new_nx, 'l': dims['l'], 's': 1.*dims['s'][0]}

#    raise Warning("This is a max problem and Sedumi format handles min problems, so the objective function has been negated and you will need to negate the result of the solve to get back the actual opt val to the relaxation.")

    sedumi_A = sparsify_tall_mat(sedumi_A)
    b_star = sparsify_tall_mat(b_star)
    sedumi_c = sparsify_tall_mat(sedumi_c)
    scipy.io.savemat(target, {'A': sedumi_A, 'b': sedumi_b, 'c': sedumi_c, 'K': sedumi_K})
    return target



def sparsify_tall_mat(M, block_height=1000):
    '''
    
    '''
    i = 0
    spmat_collector = []
    while i*block_height < M.shape[0]:
        curr_block = M[i*block_height:(i+1)*block_height, :]
        spmat_collector += [scipy.sparse.coo_matrix(curr_block.astype('d'))]
        i += 1
    return scipy.sparse.construct.vstack(spmat_collector)
        
