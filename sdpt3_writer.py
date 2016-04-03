# -*- coding: utf-8 -*-
"""
Created on Thu Mar 27 16:43:25 2014

@author: Trish


Functions which generate .mat files for SDPT3 solves
"""

from numpy import zeros
import scipy.io


def makeSDPT3Model(P_data, target, verbose=False):
    '''
    
    '''
    dims = P_data['dims']
    G_lin = 1.*P_data['G'][:dims['l'], :]
    h_lin = 1.*P_data['h'][:dims['l'], :]
    A = 1.*P_data['A']
    b = 1.*P_data['b']
    c = 1.*P_data['c']

    nums = G_lin.size[0]
    numx = G_lin.size[1]
    numeqctr = A.size[0]
    numineqctr = G_lin.size[0]
    print "\nSDP model with {0}x{0} variable matrix, {1} total variables, {2} eq ctrs, {3} ineq ctrs".format(dims['s'][0], numx, numeqctr, numineqctr)
    
    if verbose:
        print "\nSDP to Sedumi format transformation:"
        print "{0} equality constraints in {1} variables".format(numeqctr + numineqctr, nums + numx)
        print "the first {0} variables (slacks) are in the nonnegative cone".format(nums)
        print "the remaining {0} variables form a matrix in the PSD cone".format(numx)

    sedumi_A = zeros((numeqctr + numineqctr, nums + numx))
    sedumi_b = zeros((numeqctr + numineqctr, 1))


    for i in range(0, numeqctr):
        sedumi_b[i, 0] = b[i]
        for j in range(numx):
            sedumi_A[i, nums+j] = A[i, j]
    for i in range(0, numineqctr):
        sedumi_b[numeqctr+i, 0] = h_lin[i]
        sedumi_A[numeqctr+i, i] = 1.
        for j in range(numx):
            sedumi_A[numeqctr+i, nums+j] = G_lin[i,j]

    sedumi_c = zeros((1, nums + numx))
    for i in range(numx):
        sedumi_c[0, nums+i] = c[i]

    sedumi_K = {'l': dims['l'], 's': 1.*dims['s'][0]}
    k = dims['l']
    m = dims['l']
    old_col_mappings = []
    new_col_mappings = []
    for s in dims['s']:
        which_old_col = zeros((s,s))
        which_new_col = zeros((s,s))
        for i in range(s):
            for j in range(s):
                if i <= j:
                    which_old_col[i,j] = k
                    k += 1
                    which_new_col[i,j] = m
                    m += 1
                else:
                    which_old_col[i,j] = which_old_col[j,i]
                    which_new_col[i,j] = m
                    m += 1
        old_col_mappings += [which_old_col]
        new_col_mappings += [which_new_col]

    sedumi_A_expanded = zeros((numeqctr + numineqctr, m))
    sedumi_A_expanded[:, :dims['l']] = sedumi_A[:, :dims['l']]
    sedumi_c_expanded = zeros((1, m))

    for map_num in range(len(old_col_mappings)):
        which_old_col = old_col_mappings[map_num]
        which_new_col = new_col_mappings[map_num]
        for i in range(which_new_col.shape[0]):
            for j in range(i, which_new_col.shape[1]):
                sedumi_A_expanded[:, which_new_col[i,j]] += 0.5*sedumi_A[:, which_old_col[i,j]]
                sedumi_A_expanded[:, which_new_col[j,i]] += 0.5*sedumi_A[:, which_old_col[j,i]]
                sedumi_c_expanded[0, which_new_col[i,j]] += 0.5*sedumi_c[0, which_old_col[i,j]]
                sedumi_c_expanded[0, which_new_col[j,i]] += 0.5*sedumi_c[0, which_old_col[j,i]]
#    raise Warning("This is a max problem and Sedumi format handles min problems, so the objective function has been negated and you will need to negate the result of the solve to get back the actual opt val to the relaxation.")

    sedumi_A_expanded = sparsify_tall_mat(sedumi_A_expanded)
    sedumi_b = sparsify_tall_mat(sedumi_b)
    sedumi_c_expanded = sparsify_tall_mat(sedumi_c_expanded)
    scipy.io.savemat(target, {'A': sedumi_A_expanded, 'b': sedumi_b, 'c': sedumi_c_expanded, 'K': sedumi_K})

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
        
