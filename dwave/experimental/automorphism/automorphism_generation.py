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

from collections import defaultdict, deque
import random
from itertools import chain
from typing import Optional

import numpy as np
import networkx as nx
from numpy.typing import NDArray

class SchreierContext:
    """This object holds mutable states used throughout the automorphism calculation.

    Args:
        graph: A NetworkX Graph object representing the input graph.
        num_samples: Number of samples to use for generating new coset representatives
            from the existing set. If not provided, all coset representatives are used.
        seed: Seed used for reproducibility. Defaults to 42.
    """
    def __init__(self, graph: nx.Graph, num_samples: Optional[int] = None, seed: int = 42) -> None:
        if set(graph.nodes()) != set(range(len(graph.nodes()))):
            graph = nx.convert_node_labels_to_integers(graph, ordering="default")
        self._nodes: list[int] = list(graph.nodes())
        self._num_nodes: int = graph.number_of_nodes()
        self._graph_edges: list[tuple[int, int]] = list(graph.edges())
        self._num_samples: Optional[int] = num_samples
        self._rng: random.Random = random.Random(seed)
        self._leaf_nodes: int = 0
        self._nodes_reached: int = 0
        self._u_map: dict[int, int] = {}
        self._u_len: int = 0
        self._u_vector: list = []
        self._neighbours: dict[int, set[int]] = {
            n: set(graph.neighbors(n))
            for n in self._nodes
        }
        self._identity: NDArray[np.intp] = np.arange(self._num_nodes, dtype=np.intp)
        self._vertex_block_index: dict[int, int] = {n: 0 for n in graph.nodes()}

        self._best_perm: NDArray[np.intp] = np.array(
            range(self._num_nodes),
            dtype=np.intp
        )
        self._best_perm_exist: bool = False
        self._beta: NDArray[np.intp] = np.arange(self._num_nodes, dtype=np.intp)

    @property
    def leaf_nodes(self) -> int:
        """Number of leaf nodes encountered in the search tree."""
        return self._leaf_nodes

    @property
    def nodes_reached(self) -> int:
        """Total number of nodes reached during traversal of the search tree."""
        return self._nodes_reached

    @property
    def u_map(self) -> dict[int, int]:
        """Map from coset representative group index to stabilizer index."""
        return self._u_map

    @property
    def u_vector(self) -> list:
        """Coset representatives grouped by stabilizer index."""
        return self._u_vector

    @property
    def num_automorphisms(self) -> int:
        """Number of automorphisms implied by u_vector."""
        if self._u_vector:
            return int(np.prod([len(u_i) + 1 for u_i in self._u_vector], dtype=object))
        else:
            return 1

    @property
    def vertex_orbits(self):
        """Vertex orbits induced by the coset representatives in u_vector."""
        return vertex_orbits(self._u_vector, self._nodes)

    @property
    def edge_orbits(self):
        """Edge orbits induced by the coset representatives in u_vector."""
        return edge_orbits(self._u_vector, self._graph_edges)

    def _sample_from_nested(self) -> list[NDArray[np.intp]]:
        """Return a random sample of coset representatives.
        
        If num_samples is not specified, all coset representatives are returned.
        """
        generators = [g for u_vector_i in self._u_vector for g in u_vector_i]
        generators.append(np.arange(self._num_nodes))

        if not self._num_samples or len(generators) <= self._num_samples:
            return generators
        return self._rng.sample(generators, self._num_samples)

    def _test_composability(self, g: NDArray[np.intp]) -> tuple[int, NDArray[np.intp]]:
        """Test if an automorphism is composable from coset representatives.

        Based on Algorithm 6.10 from Kreher, D. L., & Stinson, D. R. (1999).
        Combinatorial algorithms: Generation, enumeration, and search.

        Modified to use a mask to skip sifting by identity permutations, which
        have no effect.

        Args:
            g: A permutation represented as a list of integers in one-line notation.

        Returns:
            A tuple (i, g_reduced) where i is the index of the first base position
            that could not be sifted. If ``g`` is completely sifted the returned index
            equals ``self._num_nodes``. ``g_reduced`` is the permutation obtained after
            sifting through all positions up to (but not including) the returned
            index.
        """
        beta = self._beta
        mask = (beta != g[beta])
        idx = mask.argmax()
        next_diff = 0

        while mask[idx]:
            next_diff += idx
            if next_diff not in self._u_map:
                return next_diff, g

            for h in self._u_vector[self._u_map[next_diff]]:
                if h[beta[next_diff]] == g[beta[next_diff]]:
                    h_valid = h
                    break
            else:
                return next_diff, g

            g = mult(inv(self._num_nodes, h_valid), g)
            mask = (beta[next_diff:] != g[beta[next_diff:]])
            idx = mask.argmax()
        return self._num_nodes, g

    def _enter(self, g: NDArray[np.intp]) -> None:
        """Add automorphism if it can't be composed from coset representatives.

        Based on Algorithm 6.11 from Kreher, D. L., & Stinson, D. R. (1999).
        Combinatorial algorithms: Generation, enumeration, and search.

        Skips entering identity permutations. If an automorphism can't be composed
        from existing coset representatives it is added to u_vector.

        Uses random-Schreier method (see Permutation Group Algorithms, Ákos Seress,
        Cambridge University Press, 2003) to attempt to compose new automorphisms
        only from a subset of randomly sampled coset representatives instead of
        the full list of coset representatives.

        In some cases the default value of ``ctx._num_samples = 3`` will not be
        sufficient to generate all automorphisms.

        The automorphisms discovered by the random-Schreier method result in pruning
        comparable to nauty, as measured by comparing the total number of search
        tree nodes visited for zephyr graphs of various sizes.

        Args:
            g: A permutation represented as a list of integers in one-line notation.
        """
        i, g = self._test_composability(g)
        if i == self._num_nodes:
            return
        if i not in self._u_map:
            self._u_map[i] = self._u_len
            self._u_len += 1
            self._u_vector.append([])
        self._u_vector[self._u_map[i]].append(g)

        if self._num_samples is None:
            # Attempt to compose new automorphisms from all coset representatives
            for u_i in self._u_vector:
                for h in u_i:
                    f = mult(g, h)
                    if (f == self._identity).all():
                        continue
                    self._enter(f)
        else:
            # Attempt to compose new automorphisms from random samples
            for h in self._sample_from_nested():
                f = mult(g, h)
                if (f == self._identity).all():
                    continue
                self._enter(f)

    def _change_base(self, beta_prime: NDArray[np.intp]) -> None:
        """Convert the set of coset representatives to a new base.

        Based on Algorithm 6.12 from Kreher, D. L., & Stinson, D. R. (1999).
        Combinatorial algorithms: Generation, enumeration, and search.

        Existing coset representatives are tested in the new basis in addition to new
        automorphisms composed from the random-Schreier process. New automorphisms
        discovered during the change of base are essential for comprehensive pruning
        of the search tree.

        Args:
            beta_prime: The new base, represented by a permutation in one-line
                notation.
        """
        u_vector_old = self._u_vector
        self._beta = beta_prime
        self._u_vector = []
        self._u_map = {}
        self._u_len = 0

        for j in range(len(u_vector_old)):
            for g in u_vector_old[j]:
                self._enter(g)

    def _refine(self, partition: list[set[int]]) -> None:
        """Perform colour refinement on partition until equitable colouring is reached.

        Based on Algorithm 7.5 from Kreher, D. L., & Stinson,
        D. R. (1999). Combinatorial algorithms: Generation, enumeration, and search.
        and Algorithms 1 and 2 from Berkholz, C. (2016). Tight lower and upper
        bounds for the complexity of canonical colour refinement.

        A stack is initialized to contain each block in the initial partition.
        An invariant h equal to the length of the intersection of the neighbourhood
        of a node with blocks popped from the stack is used to iteratively refine
        the initial partition. If a block successfully refines the partition, the
        new sub-blocks are added to the stack. Hopcroft's trick enables us to discard
        one of these blocks — a more intentional way of determining which block to
        discard may yield better performance.

        Keeping track of the neighbourhood of each block popped from the stack
        enables the refinement algorithm to be O(m log(n)) as opposed to O(n**2 log(n)),
        where m and n are edges and vertices, respectively, which significantly
        improves the algorithm for sparse graphs.

        Args:
            partition: Partition represented as a list of vertex index sets.
        """
        neighbours = self._neighbours
        vertex_block_index = self._vertex_block_index

        remaining_vertices = set(self._nodes)
        blocks_stack = deque(partition)
        while blocks_stack:
            current_block = blocks_stack.pop()
            if current_block <= remaining_vertices:
                remaining_vertices -= current_block
                touched_blocks = set()
                for v in current_block:
                    for w in neighbours[v]:
                        touched_blocks.add(vertex_block_index[w])
                vertex_block_index = self._vertex_block_index

                for block_index in sorted(touched_blocks, reverse=True):
                    count_to_vertices = defaultdict(set)
                    for u in partition[block_index]:
                        count = len(current_block & neighbours[u])
                        count_to_vertices[count].add(u)
                    num_new_blocks = len(count_to_vertices)
                    if num_new_blocks > 1:
                        len_partition = len(partition)
                        for _ in range(num_new_blocks - 1):
                            partition.append(set())
                        for count in range(len_partition - 1, block_index, -1):
                            partition[num_new_blocks - 1 + count] = partition[count]
                        new_blocks = []
                        for offset, count_key in enumerate(sorted(count_to_vertices)):
                            partition[block_index + offset] = count_to_vertices[count_key]
                            remaining_vertices.update(count_to_vertices[count_key])
                            new_blocks.append(count_to_vertices[count_key])
                        blocks_stack.extend(new_blocks[1:]) # Hopcroft's trick

                        for new_block_index in range(block_index, len(partition)):
                            for v in partition[new_block_index]:
                                vertex_block_index[v] = new_block_index

    def _compare(self, perm: NDArray[np.intp], first_split: int) -> int:
        """Compare canonical adjacency matrix against itself under a partial permutation.

        At the first differing entry, returns whether the partial permutatation has
        a greater or lesser value, otherwise it returns that they are equal.

        Based on Algorithm 7.6 from Kreher, D. L., & Stinson, D. R. (1999).
        Combinatorial algorithms: Generation, enumeration, and search.

        Args:
            perm: The permutation of the adjacency matrix to compare the canonical
                adjacency matrix against.
            first_split: The index of the first block of the partition containing
                more than one vertex, defining the size of the partial permutation
                of perm to use.

        Returns:
            An integer 0, 1, or 2 depending on whether the partial permutation
            perm results in an adjacency matrix which is less than, equal to, or
            greater than the canonical adjacency matrix, respectively.
        """
        neighbours = self._neighbours
        best_perm = self._best_perm
        for j in range(1, first_split):
            neighbours_best_j = neighbours[best_perm[j]]
            neighbours_pi_j = neighbours[perm[j]]
            for i in range(j):
                bit_best = 1 if best_perm[i] in neighbours_best_j else 0
                bit_pi = 1 if perm[i] in neighbours_pi_j else 0
                if bit_best < bit_pi:
                    return 0
                if bit_best > bit_pi:
                    return 2
        return 1

    def _canon(self, initial_partition: list[set[int]]) -> None:
        """Generate search tree based on iterative colour refinement and vertex individualization.

        Based on Algorithm 7.9 from Kreher, D. L., & Stinson, D. R. (1999).
        Combinatorial algorithms: Generation, enumeration, and search.

        Args:
            initial_partition: Partition describing the current search tree node.
        """
        self._nodes_reached += 1

        partition = list(initial_partition)
        self._refine(partition)
        # first non-singleton block index
        first_split = self._num_nodes - 1
        for i, block in enumerate(partition):
            if len(block) > 1:
                first_split = i
                break

        compare_result = 2
        if self._best_perm_exist: # if a leaf node has been reached previously
            perm_candidate = list(chain.from_iterable(partition))
            compare_result = self._compare(perm_candidate, first_split)

        if first_split == self._num_nodes - 1: # if partition is discrete
            self._leaf_nodes += 1
            if not self._best_perm_exist:
                self._best_perm_exist = True
                self._best_perm[:] = list(chain.from_iterable(partition))
            else:
                if compare_result == 2:
                    self._best_perm[:] = perm_candidate
                elif compare_result == 1:
                    perm_transformed = np.empty(self._num_nodes, dtype=np.int64)
                    perm_transformed[perm_candidate] = self._best_perm
                    self._enter(perm_transformed)

        else:
            if compare_result != 0:
                candidates = partition[first_split].copy()
                remaining_in_block = partition[first_split].copy()
                updated_partition = [None] * self._num_nodes
                for j in range(first_split):
                    updated_partition[j] = partition[j]
                for j in range(first_split + 1, len(partition)):
                    updated_partition[j + 1] = partition[j]

                while candidates:
                    vertex = next(iter(candidates))
                    updated_partition[first_split] = {vertex}
                    updated_partition[first_split + 1] = remaining_in_block - {vertex}
                    individualized_partition = [x for x in updated_partition if x is not None]

                    # update block indices
                    for idx, block in enumerate(individualized_partition):
                        for v in block:
                            self._vertex_block_index[v] = idx

                    self._canon(individualized_partition)

                    beta_prime = np.array([-1] * self._num_nodes, dtype=np.intp)
                    seen_vertices = set()
                    base_idx = -1
                    for block in individualized_partition:
                        base_idx += 1
                        rep = next(iter(block))
                        beta_prime[base_idx] = rep
                        seen_vertices.add(rep)

                    for v in self._nodes:
                        if v not in seen_vertices:
                            base_idx += 1
                            beta_prime[base_idx] = v

                    self._change_base(beta_prime)

                    candidates.discard(self._identity[vertex])
                    # remove images under generators in the first non-discrete partition
                    if first_split in self._u_map:
                        for g in self._u_vector[self._u_map[first_split]]:
                            candidates.discard(g[vertex])

def vertex_orbits(u_vector: list[list[NDArray[np.intp]]], nodes: list[int]) -> list[list[int]]:
    """Calculate vertex orbits using breadth-first search.

    If ``u_vector`` contains no coset representatives, trivial orbits are returned.

    Args:
        u_vector: Coset representatives with respect to base beta, grouped
            by stabilizer index.
        nodes: List of vertex indices used to return trivial orbits when ``u_vector`` is empty.

    Returns:
        A list of orbits, each orbit is a list of vertex indices.

    Example:
    >>> result = schreier_rep(G)
    >>> orbits = vertex_orbits(result._u_vector)
    >>> # orbits might look like [[0,2,3], [1,4]] where each sublist is an orbit
    """
    if not u_vector:
        return [[x] for x in nodes]

    if not all(isinstance(sublist, list) for sublist in u_vector):
        raise ValueError("u_vector must be a list of lists.")

    if isinstance(nodes, np.ndarray):
        nodes = nodes.tolist()

    if not isinstance(nodes, list) or not all(isinstance(n, int) for n in nodes):
        raise ValueError("nodes must be a list of integers.")

    visited = set()
    orbits = []
    num_nodes = len(nodes)
    generators = [g for u_vector_i in u_vector for g in u_vector_i]
    generators.append(np.arange(num_nodes))

    for v_start in nodes:
        if v_start in visited:
            continue

        visited.add(v_start)
        orb = [v_start]

        q = deque([v_start])
        while q:
            v_current = q.popleft()

            for g in generators:
                v_current = g[v_current]
                if v_current not in visited:
                    visited.add(v_current)
                    q.append(v_current)
                    orb.append(int(v_current))

        orbits.append(sorted(orb))

    return orbits


def edge_orbits(
        u_vector: list[list[NDArray[np.intp]]],
        edges: list[tuple[int, int]],
) -> list[list[int]]:
    """Calculate edge orbits using breadth-first search.

    Args:
        u_vector: Coset representatives with respect to base beta, grouped
            by stabilizer index.
        edges: List of graph edges as tuples of vertex index pairs.

    Returns:
        A list of orbits, each orbit is a list of edges (tuples of vertex index pairs).

    Example:
    >>> result = schreier_rep(G)
    >>> orbits = edge_orbits(G.edges(), result._u_vector)
    >>> # orbits might look like [[(0, 1), (2, 3)], [(0, 2)]] where each sublist is an orbit
    """
    if not u_vector:
        return [[x] for x in edges]

    if not all(isinstance(sublist, list) for sublist in u_vector):
        raise ValueError("u_vector must be a list of lists.")

    if not isinstance(edges, list) or not all(isinstance(e, tuple) for e in edges):
        raise TypeError("edges must be a list of tuples")

    visited = set()
    orbits = []
    generators = [g for u_vector_i in u_vector for g in u_vector_i]

    for u_start, v_start in edges:
        e_start = (u_start, v_start) if u_start < v_start else (v_start, u_start)

        if e_start in visited:
            continue

        visited.add(e_start)
        orb = [e_start]

        q = deque([e_start])
        while q:
            u, v = q.popleft()
            for g in generators:
                e_current = (g[u], g[v]) if g[u] < g[v] else (g[v], g[u])

                if e_current not in visited:
                    visited.add(e_current)
                    q.append(e_current)
                    orb.append(tuple(int(x) for x in e_current))

        orbits.append(sorted(orb))

    return orbits


def sample_automorphisms(
    u_vector: list[list[NDArray[np.intp]]],
    num_samples: int = 1,
    seed: Optional[int] = None,
) -> list[NDArray[np.intp]]:
    """Uniformly sample automorphisms from the Schreier-Sims representation.

    Randomly samples one coset representative from each non-trivial left
    transversal and takes the product, guaranteeing uniform sampling. The
    automorphisms can be composed uniformly regardless of the ordering of
    the left transversals in 'u_vector'. All products involving identity
    automorphisms are ignored.

    Args:
        u_vector: Coset representatives with respect to base beta, grouped
            by stabilizer index.
        num_samples: The number of automorphisms to return.
        seed: Random seed for reproducibility.

    Returns:
        A list of uniformly sampled automorphisms in one-line notation.

    Example:
    >>> ctx = SchreierContext(G)
    >>> automorphisms = ctx.sample_automorphisms()
    >>> # automorphisms might look like [array([2, 0, 3, 1, 6, 7, 4, 5]),
    >>> # array([5, 4, 6, 7, 0, 1, 3, 2])]
    """
    rng = np.random.default_rng(seed)
    num_nodes = len(u_vector[0][0])
    u_counts = [len(u_i) for u_i in u_vector]
    sampled_automorphisms = []

    for _ in range(num_samples):
        sample_indices = rng.integers(low=-1, high=u_counts)
        g_product = np.arange(num_nodes)

        for i in range(len(u_vector)):
            if sample_indices[i] >= 0:
                g = u_vector[i][sample_indices[i]]
                g_product = mult(g, g_product)

        sampled_automorphisms.append(g_product)

    return sampled_automorphisms


def mult(alpha: NDArray[np.intp], beta: NDArray[np.intp]) -> NDArray[np.intp]:
    """Compose two permutations in one-line notation, alpha after beta.

    Args:
        alpha: A permutation represented as a list of integers in one-line notation.
        beta: Another permutation of the same length.

    Returns:
        The composition alpha ∘ beta in one-line notation.

    Example:
        >>> alpha = np.array([2,0,1], dtype=np.intp) # (0,2,1): 0->2, 1->0, 2->1
        >>> beta  = np.array([1,2,0], dtype=np.intp) # (0,1,2): 0->1, 1->2, 2->0
        >>> mult(alpha, beta)
        array([0,1,2], dtype=intp) # (0)(1)(2): 0->0, 1->1, 2->2
    """
    return alpha[beta]


def inv(n: int, alpha: NDArray[np.intp]) -> NDArray[np.intp]:
    """Calculate the inverse of a permutation in one-line notation.

    Args:
        n: Length of permutation alpha.
        alpha: A permutation represented as a list of integers in one-line notation.

    Returns:
        The inverse of alpha in one-line notation.

    Example:
        >>> alpha = np.array([2,0,1], dtype=np.intp) # (0,2,1): 0->2, 1->0, 2->1
        >>> inv(alpha)
        np.array([1,2,0], dtype=np.intp) # (0,1,2): 0->1, 1->2, 2->0
    """
    alpha_inv = np.empty(n, dtype=np.intp)
    alpha_inv[alpha] = np.arange(n, dtype=alpha_inv.dtype)
    return alpha_inv


def schreier_rep(
        graph: nx.Graph,
        num_samples: Optional[int] = None,
        seed: int = 42
) -> SchreierContext:
    """Compute Schreier representatives and orbits for a graph.

    Builds a depth-first search tree, iteratively performing colour refinement
    and vertex individualization until leaf nodes are reached where all graph
    vertices are uniquely coloured. Leaf nodes with identical adjacency matrices
    represent graph automorphisms. Discovered automorphisms are used to prune
    the search tree.

    Args:
        graph: A NetworkX Graph object representing the input graph containing
        the following methods:
            - ``nodes()``: iterable of all nodes
            - ``number_of_nodes()``: total number of nodes
            - ``edges()``: iterable of all edges
            - ``neighbors()``: iterable of all neighbours for a given node
        num_samples: Number of samples to use for generating new coset representatives
            from the existing set. If not provided, all coset representatives are used.
        seed: Random seed for reproducibility. Defaults to 42.
    """
    ctx = SchreierContext(graph, num_samples=num_samples, seed=seed)
    initial_partition = [set(ctx._nodes)]

    ctx._canon(initial_partition)
    ctx._change_base(ctx._identity)

    return ctx


def array_to_cycle(array: NDArray[np.intp]) -> str:
    """Convert an array in one-line notation to a string in cycle notation.

    Based on Algorithm 6.4 from Kreher, D. L., & Stinson, D. R. (1999).
    Combinatorial algorithms: Generation, enumeration, and search.

    Args:
        array: The permutation in one-line notation.

    Returns:
        The permutation as a string in cycle notation.

    Example:
        >>> alpha = np.array([2,0,1], dtype=np.intp) # (0,2,1): 0->2, 1->0, 2->1
        >>> array_to_cycle(alpha)
        '(0,2,1)'
    """
    unvisited = [True] * len(array)
    cycle_parts = []

    for i in range(len(array)):
        if unvisited[i]:
            cycle_parts.append('(')
            cycle_parts.append(str(i))
            unvisited[i] = False
            j = i

            while unvisited[array[j]]:
                cycle_parts.append(',')
                j = array[j]
                cycle_parts.append(str(j))
                unvisited[j] = False

            cycle_parts.append(')')
    return ''.join(cycle_parts)
