"""
Functions which express problems in Sedumi format and export them as .mat files
for Matlab
"""

import os

import numpy as np
import scipy.io

from cvxopt import matrix as cvxmat


def write_cvxpy_to_mat(problem_data, target, simplify=True):
    '''
    Args:
        problem_data: As produced by applying get_problem_data['CVXOPT'] to a
        cvxpy problem.

    Returns: (None)

    Effect:
        Saves a .mat file containing the A, b, c, K that define the problem
        in Sedumi format to target (see http://plato.asu.edu/ftp/usrguide.pdf)
    '''

    A, b, c, K, offset = make_sedumi_format_problem(
        problem_data, simplify=simplify)
    assert offset == 0
    write_sedumi_to_mat(A, b, c, K, target)


def write_sedumi_to_mat(A, b, c, K, target):
    '''
    Args:
        A, b, c, K for Sedumi format
        target: the path where we will save the .mat

    Effect:
        Saves a .mat file containing A, b, c, K to target
    '''
    A = sparsify_tall_mat(A)
    b = sparsify_tall_mat(b)
    c = sparsify_tall_mat(c)
    K = clean_K_dims(K)

    # Check that target folder exists
    folder = os.path.dirname(target)
    if not os.path.exists(folder):
        os.makedirs(folder)

    scipy.io.savemat(target, {'A': A, 'b': b, 'c': c, 'K': K})


def clean_K_dims(K):
    '''
    Matlab requires the dimensions to be given in floating point numbers,
    this checker ensures that they are.
    '''
    for p in K:
        # let's try treating this like a list or tuple, and if that falls
        # through then we'll assume it's a single number instead.
        if isinstance(K[p], list):
            for i, x in enumerate(K[p]):
                K[p][i] = 1. * x
        else:
            K[p] = 1. * K[p]
    return K


def problem_data_prep(problem_data):
    '''
    'Touch up' the problem data in the following ways:
      - Make sure the matrix elements aren't integers
      - Make sure they're dense matrices rather than sparse ones, otherwise
        there seem to be difficulties constructing block matrices
      - Transpose c to be a row vector, which matches the organization of A, b, G, h
        (rows are for constraints, columns are for variables)
    '''
    problem_data['A'] = cvxmat(1. * problem_data['A'])
    problem_data['b'] = cvxmat(1. * problem_data['b'])
    problem_data['G'] = cvxmat(1. * problem_data['G'])
    problem_data['h'] = cvxmat(1. * problem_data['h'])
    problem_data['c'] = cvxmat(1. * problem_data['c']).T
    return problem_data


def make_sedumi_format_problem(problem_data, simplify=True):
    '''
    Input:
        problem_data: As produced by applying get_problem_data['CVXOPT'] to a
        cvxpy problem.
    Returns:
        A, b, c, K: Data defining an equivalent problem in Sedumi format.
    '''
    problem_data = problem_data_prep(problem_data)
    dims = problem_data['dims']
    assert not dims[
        'q'], "Sorry, at this time we can't handle SOC constraints!"

    nx = len(problem_data['c'])
    ni = dims['l']
    ne = len(problem_data['b'])
    num_sdp_vars = sum([s * s for s in dims['s']])

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

    c = np.zeros((1, num_sedumi_vars))
    c[0, 0:nx] = problem_data['c']

    A = np.zeros((ne + ni + num_sdp_vars, num_sedumi_vars))
    b = np.zeros((ne + ni + num_sdp_vars, 1))

    # Fill in blocks for Ax = b constraints
    A[0:ne, 0:nx] = problem_data['A']
    b[0:ne] = problem_data['b']

    # Fill in blocks for Gx + s = h
    A[ne:ne + ni, 0:nx] = problem_data['G'][:ni, :]  # = Gl
    A[ne:ne + ni, nx:nx + ni] = np.eye(ni)
    b[ne:ne + ni] = problem_data['h'][:ni, :]  # = hl

    # Fill out blocks defining h - Gs = vec(Y), where Y is the PSD matrix
    A[ne + ni:, 0:nx] = problem_data['G'][ni:, :]  # = Gs
    A[ne + ni:, nx + ni:] = np.eye(num_sdp_vars)
    b[ne + ni:] = problem_data['h'][ni:, :]  # = hs

    obj_cst = 0.
    K = {'f': nx, 'l': dims['l'], 'q': [], 's': dims['s']}
    if simplify:
        A, b, c, K, obj_cst = simplify_sedumi_model(A,
                                                    b,
                                                    c,
                                                    K,
                                                    allow_nonzero_b=False)
        assert obj_cst == 0, "This shouldn't be possible with allow_nonzero_b=False."
    else:
        A, b, c, K = symmetrize_sedumi_model(A, b, c, K)
    return A, b, c, K, obj_cst


def symmetrize_sedumi_model(A, b, c, K):
    '''
    Symmetrize sedumi model.
    '''
    colstart = K['f'] + K['l'] + sum(K['q'])

    for s in K['s']:
        for i in range(s):
            for j in range(i + 1, s):
                ijcol = colstart + i * s + j
                jicol = colstart + j * s + i
                averaged_Acol = 0.5 * (A[:, ijcol] + A[:, jicol])
                A[:, ijcol] = averaged_Acol
                A[:, jicol] = averaged_Acol
                averaged_c = 0.5 * (c[0, ijcol] + c[0, jicol])
                c[0, ijcol] = averaged_c
                c[0, jicol] = averaged_c
        colstart + s**2
    return A, b, c, K


def simplify_sedumi_model(A, b, c, K, allow_nonzero_b=False):
    '''
    Tries to eliminate variables using a few simple strategies:

    1. If a constraint is expressing :math:`A_{ki}x_i = b_k` where variable
    :math:`x_i` is a free variable, we can eliminate :math:`x_i`.

    2. If a constraint is expressing :math:`A_{ki}x_i + A_{kj}x_j = b_k`
    where variable :math:`x_i` is a free variable, we can eliminate
    :math:`x_i`.

    Args:
        A, b, c, K: for a problem in Sedumi format
        allow_nonzero_b: If False, only eliminate if bk = 0 is zero

    Returns:
        A, b, c, K: for the simplified problem.
        offset: A constant which must be added to the optimal value of the
        simplified problem in order to make it equivalent.  With
        allow_nonzero_b, offset will be 0.
    '''
    n_free = K['f']  # the first n_free variables will be eligible for any kind
    # of elimination
    n_nonneg = K['l']  # the next n_nonneg variables will be eligible for only
    # the simplest substitution aij*xj=bi and only in the case
    # where bi/aij >=0.
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
    offset = 0
    # Given var_i which is a free variable, figure out if there is a row k of
    # G_star such that Gs_star[ctr_k, var_i] == -1 AND hs[ctr_k] == 0 AND the
    # only other non-zero element in the row is Gs_star[ctr_k, nx + ni +
    # ctr_k] == 1
    for ctr_k in range(n_ctr):
        i, j = check_eliminatibility(A[ctr_k, :],
                                     b[ctr_k, 0],
                                     n_elig=n_free + n_nonneg,
                                     allow_nonzero_b=allow_nonzero_b)
        # Two cases where we can eliminate xi:
        # 1) xi is a free var
        free_ok = (i is not None and i < n_free)
        # 2) xi is a nonneg var, the ctr is of form Akixi = bk, and bk/Aki >= 0
        nonneg_ok = (i is not None and j is None and 1. *
                     b[ctr_k, 0] / A[ctr_k, i] >= 0)

        if free_ok or nonneg_ok:
            aki = A[ctr_k, i]
            bk = b[ctr_k, 0]
            factor = 1. * bk / aki

            # Akixi (optionally + Akjxj) = bk case, eliminate xi using
            # xi = (Akj/Aki) - (bk/Aki)*x_j
            b[:, 0] += -factor * A[:, i]
            offset += factor * c[0, i]

            if j is not None:
                # Akixi + Akjxj = bk case
                akj = A[ctr_k, j]
                factor = 1. * akj / aki
                A[:, j] += -factor * A[:, i]
                c[0, j] += -factor * c[0, i]

            # zero out the coefficients of var i to make sure it isn't chosen
            # for elimination again
            A[:, i] *= 0.
            c[0, i] *= 0.

    # To wrap up, list all the variables which are still nontrivial to the
    # model
    n_deleted_f = 0
    n_deleted_l = 0
    cols_to_keep = []
    vars_fl = n_free + n_nonneg
    for col in range(vars_fl):
        # free vars not in constraints must have 0 coeff in obj, else unbounded.
        # nonneg vars not in constraints must have >=0 coeff in obj, else unbounded.
        # if a var makes the probblem unbounded, we'll leave it alone and let
        # the user find out when they actually solve.
        free_and_deletable = col < n_free and c[0, col] == 0
        nneg_and_deletable = col >= n_free and col < vars_fl and c[0, col] >= 0
        if free_and_deletable and not abs(A[:, col]).any():
            n_deleted_f += 1
        elif nneg_and_deletable and not abs(A[:, col]).any():
            n_deleted_l += 1
        else:
            cols_to_keep.append(col)

    # SOC vars eliminatable iff they're not the first var of their vector and
    # they're unused in any ctrs.
    col_start = n_free + n_nonneg

    for i, q_size, in enumerate(K['q']):
        cols_to_keep.append(col_start)
        for col in range(col_start + 1, col_start + q_size):
            if c[0, col] == 0 and not abs(A[:, col]).any():
                K['q'][i] += -1
            else:
                cols_to_keep.append(col)
        col_start += q_size

    # All SDP vars kept
    cols_to_keep += range(col_start, n_vars)

    # Symmetrize the use of PSD matrix variables.  We do this now because it might
    # zero out some additional ctrs which we'll check for next.
    A, b, c, K = symmetrize_sedumi_model(A, b, c, K)

    # Now figure out which ctrs are nontrivial (trivial meaning 0x = 0).
    # Note that A ctr of 0x = b would make the problem infeasible, but in that case
    # we'll leave it in so the user finds it when they solve.
    rows_to_keep = []
    for row in range(n_ctr):
        if b[row, 0] != 0 or abs(A[row, :]).any():
            rows_to_keep.append(row)
#==============================================================================
#   SIMPLIFICATION STEP PART TWO: construct final matrices with only
#     the rows/cols we want
#==============================================================================
    # new downsized problem
    A = A[np.ix_(rows_to_keep, cols_to_keep)]
    b = b[np.ix_(rows_to_keep, [0])]
    c = c[np.ix_([0], cols_to_keep)]

    # problem dimensions
    assert len(cols_to_keep) + n_deleted_f + n_deleted_l
    K = {'f': K['f'] - n_deleted_f,
         'l': K['l'] - n_deleted_l,
         'q': K['q'],
         's': K['s']}
    return A, b, c, K, offset


def check_eliminatibility(g, h, n_elig=None, allow_nonzero_b=False):
    '''
    Tests if constraint :math:`gx = h` fits either pattern :math:`ax_i = d`
    or pattern :math:`ax_i + bx_j = d`, with the requirement that the
    :math:`x_i` variable be one of the first n_elig variables.

    Returns:
       ``i, None`` such that the constraint has the form :math:`ax_i = d` for
       some :math:`a, d`.

       ``i, j`` such that the constraint has the form :math:`ax_i + bx_j = d`
       for some :math:`a, b, d`.

       ``None, None`` if neither pattern applies.
    '''
    n = len(g)

    if n_elig is None:
        n_elig = n

    if not allow_nonzero_b and h != 0:
        return None, None

    for i in range(n_elig):
        if g[i] != 0:
            j = i + 1
            while j < n and g[j] == 0:
                j += 1
            # having stopped, see which we have found:
            if j == n:
                return i, None  # the end of the row
            elif not abs(g[j + 1:]).any():
                return i, j  # the second of exactly two nonzero coefficients
            else:
                return None, None  # the second of three or more nonzero coefficients

    # If nothing's been returned yet, it's because all the eliminatible
    # vars' coeffs are zero.
    return None, None


def sparsify_tall_mat(M, block_height=1000):
    '''
    Returns a sparse matrix in scipy.sparse.coo_matrix form which is equivalent to M
    '''
    i = 0
    spmat_collector = []
    while i * block_height < M.shape[0]:
        curr_block = M[i * block_height:(i + 1) * block_height, :]
        spmat_collector += [scipy.sparse.coo_matrix(curr_block.astype('d'))]
        i += 1
    return scipy.sparse.construct.vstack(spmat_collector)
