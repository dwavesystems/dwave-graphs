# Copyright 2025 D-Wave
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from functools import lru_cache
from collections import defaultdict, deque
from operator import itemgetter
import random

class SchreierContext:
    def __init__(self, G, num_samples=3, seed=42):
        self.G = G
        self.n = G.number_of_nodes()
        self.num_samples = num_samples
        self.rng = random.Random(seed)

        # Precompute neighbors as sets for fast membership
        self.G_neighbours = {i: set(G.neighbors(i)) for i in range(self.n)}

        # Initialize Identity permutation
        self.I = tuple(range(self.n))

        # Partition bookkeeping
        self.vertex_to_block = [0] * self.n

        # Canonical labeling state
        self.Best = list(range(self.n))
        self.BestExist = False

        # Group vector initialization
        self.G_vector = [self.I, [set() for _ in range(self.n)]]

    @staticmethod
    def sample_from_nested(nested, rng, k):
        # Avoid repeated attribute lookups in tight loops
        all_items = [item for bucket in nested for item in bucket]
        if not all_items:
            return []
        if len(all_items) <= k:
            return all_items.copy()
        return rng.sample(all_items, k)
    
    
@lru_cache(maxsize=None)
def mult(alpha, beta):
    # alpha, beta must be tuples; returns a tuple of alpha indexed by beta
    return itemgetter(*beta)(alpha)

@lru_cache(maxsize=None)
def inv(n, alpha):
    # alpha must be a tuple
    beta = [0] * n
    for i in range(n):
        beta[alpha[i]] = i
    return tuple(beta)

def test(ctx, g):
    n = ctx.n
    I = ctx.I
    beta = ctx.G_vector[0]
    U = ctx.G_vector[1]

    for i in range(n):
        bi = beta[i]
        if I[bi] == g[bi]: # Identity won't sift
            continue 
        Ui = U[i]
        h_valid = None
        for h in Ui:
            if h[bi] == g[bi]:
                h_valid = h
                break
        if h_valid is not None:
            pi_2 = inv(n, h_valid)
            g = mult(pi_2, g)
            if g == I:
               return n, g
        else:
            return i, g
    return n, g

def enter(ctx, g):
    n = ctx.n
    U = ctx.G_vector[1]

    i, g = test(ctx, g)
    if i == n:
        return
    else:
        U[i].add(g)

    # Try to compose new generators from random samples of existing generators
    for h in SchreierContext.sample_from_nested(U, ctx.rng, ctx.num_samples):
        if g == h:
            continue
        f = mult(g, h)
        enter(ctx, f)

def change_base(ctx, beta_prime):
    n = ctx.n

    U_vector_prime = [set() for _ in range(n)]
    H_vector = [tuple(beta_prime), U_vector_prime]

    # Re-enter existing generators into new base
    old_U = ctx.G_vector[1]
    ctx.G_vector[:] = H_vector  # Switch to new base
    for j in range(n):
        for g in old_U[j]:
            enter(ctx, g)

def split_and_update(ctx, B, j, T, S, U):
    G_neighbours = ctx.G_neighbours
    vertex_to_block = ctx.vertex_to_block

    L = defaultdict(set)
    Bj = B[j]
    for u in Bj:
        h = len(T & G_neighbours[u])
        L[h].add(u)

    m = len(L)
    if m > 1:
        len_B = len(B)
        # Expand B
        for _ in range(m - 1):
            B.append(set())
        # Shift tail to make space
        for h in range(len_B - 1, j, -1):
            B[m - 1 + h] = B[h]
        # Fill splits
        S_temp = []
        k = 0
        for hkey in sorted(L):
            B[j + k] = L[hkey]
            U.update(L[hkey])
            S_temp.append(L[hkey])
            k += 1
        # Push in reverse order
        S.extend(reversed(S_temp))
        # Update vertex_to_block
        for new_block_index in range(j, len(B)):
            for v in B[new_block_index]:
                vertex_to_block[v] = new_block_index
    return U

def refine(ctx, A, B):
    G = ctx.G
    G_neighbours = ctx.G_neighbours
    vertex_to_block = ctx.vertex_to_block

    U = set(G.nodes())
    S = deque(B)
    # Process stack
    while S:
        T = S.pop()
        if T <= U:
            U -= T
            touched_blocks = set()
            # collect touched blocks
            for v in T:
                for w in G_neighbours[v]:
                    touched_blocks.add(vertex_to_block[w])
            # split touched in reverse order
            for j in sorted(touched_blocks, reverse=True):
                U = split_and_update(ctx, B, j, T, S, U)

def compare(ctx, pi, l):
    neighbours = ctx.G_neighbours
    Best = ctx.Best
    for j in range(1, l):
        Best_j = Best[j]
        pi_j = pi[j]
        neighbours_best_j = neighbours[Best_j]
        neighbours_pi_j = neighbours[pi_j]
        for i in range(j):
            x = 1 if Best[i] in neighbours_best_j else 0
            y = 1 if pi[i] in neighbours_pi_j else 0
            if x < y:
                return 0
            if x > y:
                return 2
    return 1

def canon(ctx, P):
    n = ctx.n
    G = ctx.G

    Q = list(P)
    refine(ctx, P, Q)

    # first non-singleton block index
    l = n - 1
    for i, block in enumerate(Q):
        if len(block) > 1:
            l = i
            break

    Res = 2
    if ctx.BestExist:
        pi_1 = [x for s in Q for x in s]
        Res = compare(ctx, pi_1, l)

    len_Q = len(Q)
    if len_Q == n:
        if not ctx.BestExist:
            ctx.BestExist = True
            ctx.Best[:] = [x for s in Q for x in s]
        else:
            if Res == 2:
                ctx.Best[:] = pi_1 
            elif Res == 1:
                pi_2 = [0] * n
                for i in range(n):
                    pi_2[pi_1[i]] = ctx.Best[i]
                enter(ctx, tuple(pi_2))
    else:
        if Res != 0:
            #true_len_Q = len(Q)
            C = Q[l].copy()
            D = Q[l].copy()
            R = [None] * n
            for j in range(l):
                R[j] = Q[j]
            for j in range(l + 1, len_Q):
                R[j + 1] = Q[j]

            while C:
                u = next(iter(C))
                R[l] = {u}
                R[l + 1] = D - {u}
                R_compact = [x for x in R if x is not None]
                # update block indices
                vtb = ctx.vertex_to_block
                for idx, block in enumerate(R_compact):
                    for v in block:
                        vtb[v] = idx
                canon(ctx, R_compact)

                beta_prime = [None] * n
                
                for j in range(l + 1):
                    rep = next(iter(R_compact[j]))
                    beta_prime[j] = rep
                    
                for y in G.nodes():
                    if y not in beta_prime:
                        j += 1
                        beta_prime[j] = y

                change_base(ctx, beta_prime)
                C -= {ctx.I[u]}
                # remove images under generators in the l-th bucket
                for g in ctx.G_vector[1][l]:
                    C -= {g[u]}

def schreier_rep(G, num_samples=3, seed=42):
    ctx = SchreierContext(G, num_samples=num_samples, seed=seed)

    # Initial partition: single block with all vertices
    P = [set(G.nodes())]

    canon(ctx, P)
    change_base(ctx, ctx.I)
    return ctx.G_vector

def ArrayToCycle(A):
    P = [True] * len(A)
    C = ''
    for i in range(len(A)):
        if P[i]:
            C += '('
            C += str(i)
            P[i] = False
            j = i
            while P[A[j]]:
                C += ','
                j = A[j]
                C += str(j)
                P[j] = False
            C += ')'
    return C