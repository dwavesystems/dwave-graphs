from collections import defaultdict, deque
import random
from itertools import chain
from typing import List, Set, Tuple, Dict, Optional
import numpy as np
import networkx as nx
from numpy.typing import NDArray

class SchreierContext:
    """This object holds mutable states used throughout the automorphism calculation.

    Attributes:
        - graph: A NetworkX Graph object representing the input graph.
        - num_nodes: Number of vertices in the graph.
        - num_samples: Number of random coset representatives to sample for the 
        Random-Schreier method.
        - rng: A random number generator instance used for sampling.
        - leaf_nodes: Number of leaf nodes encountered in the search tree.
        - nodes_reached: Total number of nodes reached during traversal of the
        search tree.
        - u_map: A dictionary mapping the index of each group of coset representatives
        in u_vector to their stabilizer index. 
        - u_len = The number of groups of non-trivial coset representatives 
        (containing permutations other than the identity).
        - u_vector: coset representatives with respect to base beta, grouped by
        stabilizer index.
        - neighbours: A precomputed dictionary of vertex neighbours for fast
        membership.
        - identity: A precomputed identity permutation for fast comparsion.
        - vertex_block_index = A map of each vertex to which block of the
        partition it is found in.
        - best: The first permutation reached that yields the largest 
        adjacency-matrix reading found so far.
        - best_exist: Indicates whether any leaf node in the search tree has
        been reached.
        - beta: The current base, used as a reference permutation.
    """
    def __init__(
            self,
            graph: nx.Graph,
            num_samples: int = 3,
            seed: int = 42
    ) -> None:
        """
        Initialize SchreierContext.
    
        Args:
            graph: A NetworkX Graph object representing the input graph.
            num_samples: Number of randomly sampled automorphisms to return.
            seed: Seed used for reproducibility. Defaults to 42.
        """        
        self.graph: nx.Graph = graph
        self.num_nodes: int = graph.number_of_nodes()
        self.num_samples: int = num_samples
        self.rng: random.Random = random.Random(seed)
        self.leaf_nodes: int = 0
        self.nodes_reached: int = 0
        self.u_map: dict[int, int] = {}
        self.u_len: int = 0
        self.u_vector: list[list[NDArray[np.intp]]] = []
        self.idx_to_node: dict[int, int] = {
            idx: n for idx, n in enumerate(graph.nodes())
        }
        self.neighbours: dict[int, set[int]] = {
            self.idx_to_node[i]: set(graph.neighbors(self.idx_to_node[i]))
            for i in range(self.num_nodes)
        }
        self.identity: NDArray[np.intp] = np.array(
            range(self.num_nodes),
            dtype=np.intp
        )
        self.vertex_block_index: list[int] = [0] * self.num_nodes
        self.vertex_block_index: dict[int, int] = {n: 0 for n in graph.nodes()}

        self.best_perm: NDArray[np.intp] = np.array(
            range(self.num_nodes),
            dtype=np.intp
        )
        self.best_perm_exist: bool = False
        self.beta: NDArray[np.intp] = np.array(
            range(self.num_nodes),
            dtype=np.intp)

    def _sample_from_nested(self) -> list[NDArray[np.intp]]:
        """Return a random sample of coset representatives.

        Args:
            ctx: A context object containing the following attributes:
                - u_vector: coset representatives with respect to base beta, grouped 
                by stabilizer index.
                - num_samples: Number of randomly sampled automorphisms to return.
                - rng: A random number generator instance used for sampling.
        """
        generators = [g for u_vector_i in self.u_vector for g in u_vector_i]
        generators.append(np.array(tuple(range(self.num_nodes))))
        if not generators:
            return []
        if len(generators) <= self.num_samples:
            return generators
        return self.rng.sample(generators, self.num_samples)
        
    def _test(self, g: NDArray[np.intp]) -> tuple[int, NDArray[np.intp]]:
        """Test if an automorphism is composable from coset representatives. 
        
        Based on Algorithm 6.10 from Kreher, D. L., & Stinson, D. R. (1999). 
        Combinatorial algorithms: Generation, enumeration, and search. 
        Sifting operations using identity permutations are skipped by
        using a mask to fo find the first non-trivial sifting operation. 
        
        Args:
            ctx: A context object containing the following attributes:
                - beta: The current base, used as a reference permutation.
                - u_vector: coset representatives with respect to base beta, grouped 
                by stabilizer index.
                - u_map: A dictionary mapping the index of each group of left
                transversals in u_vector to their stabilizer index. 
                - num_nodes: The size of the permutation group.
            g: A permutation represented as a list of integers in one-line notation.

        Returns:
            A tuple (i, g_reduced) where i is the index of the first base position
            that could not be sifted. If g is completely sifted the returned index
            equals self.num_nodes. g_reduced is the permutation obtained after
            sifting through all positions up to (but not including) the returned
            index.
        """
        beta = self.beta
        mask = (beta != g[beta])
        next_diff = mask.argmax()

        while True:
            if next_diff in self.u_map:
                u_vector_i = self.u_vector[self.u_map[next_diff]]
            else:
                return next_diff, g
            h_valid = None
            for h in u_vector_i:
                if h[beta[next_diff]] == g[beta[next_diff]]:
                    h_valid = h
                    break
                
            if h_valid is not None:
                g = mult(inv(self.num_nodes, h_valid), g)
                mask = (beta[next_diff:] != g[beta[next_diff:]])
                if mask.any():
                    next_diff += mask.argmax()
                else:
                    break
            else:
                return next_diff, g
        return self.num_nodes, g

    def _enter(self, g: NDArray[np.intp]) -> None:
        """Add automorphism if it can't be composed from coset representatives. 
        
        Based on Algorithm 6.11 from Kreher, D. L., & Stinson, D. R. (1999).
        Combinatorial algorithms: Generation, enumeration, and search.
        Skips entering identity permutations. 

        Uses random-Schreier method (see Permutation Group Algorithms, Ákos Seress, 
        Cambridge University Press, 2003) to attempt to compose new automorphisms
        only from a subset of randomly sampled coset representatives instead of
        the full list of coset representatives. 

        In some cases the default value of ctx.num_samples = 3 will not be sufficient
        to generate all automorphisms.
        
        The automorphisms discovered by the Random-Schreier method result in pruning
        comparable to nauty, as measured by comparing the total number of search
        tree nodes visited for zephyr graphs of various sizes. 
        
        Args:
            ctx: A context object containing the following attributes:
                - u_vector: coset representatives with respect to base beta, grouped 
                by stabilizer index.
                - u_map: A dictionary mapping the index of each group of left
                transversals in u_vector to their stabilizer index. 
                - n: The size of the permutation group.
                - u_len = The number of groups of non-trivial coset representatives 
                (containing permutations other than the identity).
                - identity: A precomputed identity permutation for fast comparison.
            g: A permutation represented as a list of integers in one-line notation.
        """
        i, g = self._test(g)
        if i == self.num_nodes:
            return
        else:
            if i not in self.u_map:
                self.u_map[i] = self.u_len
                self.u_len += 1
                self.u_vector.append([])
            self.u_vector[self.u_map[i]].append(g)

        if self.num_samples is None:
            # Attempt to compose new automorphisms from all transversals 
            for u_i in self.u_vector:
                for h in u_i:
                    f = mult(g, h)
                    if (f == self.identity).all(): 
                        continue       
                    self._enter(f)
        else:
            # Attempt to compose new automorphisms from random samples 
            for h in self._sample_from_nested():
                f = mult(g, h)
                if (f == self.identity).all(): 
                    continue       
                self._enter(f)

    def _change_base(self, beta_prime: NDArray[np.intp]) -> None:
        """Convert the set of coset representatives to a new base.
        
        Based on Algorithm 6.12 from Kreher, D. L., & Stinson, D. R. (1999).
        Combinatorial algorithms: Generation, enumeration, and search.
        
        Existing coset representatives are tested in the new basis in addition to new
        automorphisms composed from the Random-Schreier process. New automorphisms
        discovered during the change of base are essential for comprehensive pruning
        of the search tree.
        
        Args:
            ctx: A context object containing the following attributes:
                - beta: The current base, used as a reference permutation.
                - u_vector: coset representatives with respect to base beta, grouped 
                by stabilizer index.
                - u_map: A dictionary mapping the index of each group of left
                transversals in u_vector to their stabilizer index. 
                - n: The size of the permutation group.
                - u_len = The number of groups of non-trivial coset representatives 
                (containing permutations other than the identity).
            beta_prime: The new base, represented by a permutation in one-line 
            notation.
        """
        u_vector_old = self.u_vector
        self.beta = beta_prime
        self.u_vector = []
        self.u_map = {}
        self.u_len = 0
    
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
            ctx: A context object containing the following attributes: 
                - neighbours: A precomputed dictionary of vertex neighbours for fast
                membership.
                - vertex_block_index = A map of each vertex to which block of the 
                partition it is found in.
            partition: Partition represented as a list of vertex index sets.
        """
        neighbours = self.neighbours
        vertex_block_index = self.vertex_block_index

        remaining_vertices = set(self.graph.nodes())
        blocks_stack = deque(partition)
        while blocks_stack:
            current_block = blocks_stack.pop()
            if current_block <= remaining_vertices:
                remaining_vertices -= current_block
                touched_blocks = set()
                for v in current_block:
                    for w in neighbours[v]:
                        touched_blocks.add(vertex_block_index[w])
                vertex_block_index = self.vertex_block_index

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
                        offset = 0
                        for count_key in sorted(count_to_vertices):
                            partition[block_index + offset] = count_to_vertices[count_key]
                            remaining_vertices.update(count_to_vertices[count_key])
                            new_blocks.append(count_to_vertices[count_key])
                            offset += 1
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
            ctx: A context object containing the following attributes: 
                - neighbours: A precomputed dictionary of vertex neighbours for fast
                membership.
                - best: The canonical permutation producing the largest adjacency
                matrix discovered so far.
            perm: The permutation of the adjacency matrix to compare the canonical
            adjacency matrix against.
            first_split: The index of the first block of the partition containing 
            more than one vertex, defining the size of the partial permutation of perm to use.

        Returns:
            An integer 0, 1, or 2 depending on whether the partial permutation
            perm results in an adjacency matrix which is less than, equal to, or 
            greater than the canonical adjacency matrix, respectively.
        """
        neighbours = self.neighbours
        best_perm = self.best_perm
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
            ctx: A context object containing the following attributes: 
                - nodes_reached: Tracks how many nodes the search tree has reached.
                - num_nodes: The size of the permutation group.
                - best_perm_exist: Indicates whether any leaf node in the search tree has
                been reached.
                - best_perm: The first permutation reached that yields the largest 
                adjacency-matrix reading found so far.
                - vertex_block_index = A map of each vertex to which block of the 
                partition it is found in.
                - u_vector: coset representatives with respect to base beta, grouped 
                by stabilizer index.
                - u_map: A dictionary mapping the index of each group of left
                transversals in u_vector to their stabilizer index. 
            initial_partition: Partition describing the current search tree node.
        """
        self.nodes_reached += 1

        partition = list(initial_partition)
        self._refine(partition)
        # first non-singleton block index
        first_split = self.num_nodes - 1
        for i, block in enumerate(partition):
            if len(block) > 1:
                first_split = i
                break

        compare_result = 2
        if self.best_perm_exist: # if a leaf node has been reached previously
            perm_candidate = list(chain.from_iterable(partition))
            compare_result = self._compare(perm_candidate, first_split)

        if first_split == self.num_nodes - 1: # if partition is discrete
            self.leaf_nodes += 1
            if not self.best_perm_exist:
                self.best_perm_exist = True
                self.best_perm[:] = list(chain.from_iterable(partition))
            else:
                if compare_result == 2:
                    self.best_perm[:] = perm_candidate 
                elif compare_result == 1:
                    perm_transformed = np.empty(self.num_nodes, dtype=np.int64)
                    perm_transformed[perm_candidate] = self.best_perm
                    self._enter(perm_transformed)
                    
        else:
            if compare_result != 0:
                candidates = partition[first_split].copy()
                remaining_in_block = partition[first_split].copy()
                updated_partition = [None] * self.num_nodes
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
                            self.vertex_block_index[v] = idx

                    self._canon(individualized_partition)

                    beta_prime = np.array([-1] * self.num_nodes, dtype=np.intp)
                    seen_vertices = set()
                    base_idx = -1
                    for block in individualized_partition:
                        base_idx += 1
                        rep = next(iter(block))
                        beta_prime[base_idx] = rep
                        seen_vertices.add(rep)

                    for v in self.graph.nodes():
                        if v not in seen_vertices:
                            base_idx += 1
                            beta_prime[base_idx] = v
                            
                    self._change_base(beta_prime)

                    candidates.discard(self.identity[vertex])
                    # remove images under generators in the first non-discrete partition
                    if first_split in self.u_map:
                        for g in self.u_vector[self.u_map[first_split]]:
                            candidates.discard(g[vertex])

def vertex_orbits(u_vector: list[list[NDArray[np.intp]]]) -> list[list[int]]:
    """Calculate vertex orbits using breadth-first search.

    Args:
        u_vector: coset representatives with respect to base beta, grouped 
        by stabilizer index.

    Returns:
        A list of orbits, each orbit is a list of vertex indices.

    Example:
    >>> result = schreier_rep(G)
    >>> orbits = vertex_orbits(result.u_vector)
    >>> # orbits might look like [[0,2,3], [1,4]] where each sublist is an orbit
    """  
    visited = set()
    orbits = []
    num_nodes = len(u_vector[0][0])
    generators = [g for u_vector_i in u_vector for g in u_vector_i]
    generators.append(np.array(tuple(range(num_nodes))))
    for v_start in range(num_nodes):
        if v_start in visited:
            continue
        q = deque([v_start])
        visited.add(v_start)
        orb = [v_start]
        while q:
            v_start = q.popleft()
            for g in generators:
                v_current = g[v_start]
                if v_current not in visited:
                    visited.add(v_current)
                    q.append(v_current)
                    orb.append(int(v_current))
        orbits.append(sorted(orb))
    return orbits


def edge_orbits(
        edges: list[tuple[int, int]],
        u_vector: list[list[NDArray[np.intp]]]
) -> list[list[int]]:
    """Calculate edge orbits using breadth-first search.

    Args:
        u_vector: coset representatives with respect to base beta, grouped 
        by stabilizer index.

    Returns:
        A list of orbits, each orbit is a list of vertex indices.

    Example:
    >>> result = schreier_rep(G)
    >>> orbits = edge_orbits(G.edges(), result.u_vector)
    >>> # orbits might look like [[0,4], [1,2,3]] where each sublist is an orbit
    """
    visited = set()
    orbits = []
    num_nodes = len(u_vector[0][0])
    generators = [g for u_vector_i in u_vector for g in u_vector_i]
    generators.append(np.array(tuple(range(num_nodes))))

    for e_start in edges:
        e_start = tuple(sorted(e_start))
        if e_start in visited:
            continue
        q = deque([e_start])
        visited.add(e_start)
        orb = [e_start]
        while q:
            e_start = q.popleft()
            for g in generators:
                e_current = tuple(sorted((int(g[e_start[0]]), int(g[e_start[1]]))))
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
    """Uniformly sample automorphisms from the Sims-Schreier representation.

    Randomly samples one coset representative from each non-trivial left
    transversal and takes the product, guaranteeing uniform sampling. The
    automorphisms can be composed uniformly regardless of the ordering of
    the left transversals in 'u_vector'. All products involving identity
    automorphisms are ignored.

    Args:
        u_vector: coset representatives with respect to base beta, grouped 
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
        g_product = np.array(range(num_nodes))
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
) -> "SchreierContext":
    """Compute Schreier representatives and orbits for a graph. 

    Builds a depth-first search tree, iteratively performing colour refinement
    and vertex individualization until leaf nodes are reached where all graph
    vertices are uniquely coloured. Leaf nodes with identical adjacency matrices
    represent graph automorphisms. Discovered automorphisms are used to prune
    the search tree. 

    Args:
        graph: A NetworkX Graph object representing the input graph.
        Must provide a .nodes() iterable and standard NetworkX graph methods.
        num_samples: Number of samples used to compose new automorphisms 
        according to the Random-Schreier method.
        seed: Random seed for reproducibility. Defaults to 42.
    """
    ctx = SchreierContext(graph, num_samples=num_samples, seed=seed)
    initial_partition = [set(graph.nodes())]

    ctx._canon(initial_partition)
    ctx._change_base(ctx.identity)

    ctx.vertex_orbits = vertex_orbits(ctx.u_vector)
    ctx.edge_orbits = edge_orbits(graph.edges(), ctx.u_vector)
    ctx.num_automorphisms = int(np.prod([len(u_i) + 1 for u_i in ctx.u_vector], dtype=object))
    return ctx


def array_to_cycle(array: NDArray[np.intp]):
    """Convert an array in one-line notation to a string in cycle notation.

    Based on Algorithm 6.4 from Kreher, D. L., & Stinson, D. R. (1999).
    Combinatorial algorithms: Generation, enumeration, and search. 

    Args:
        array: The permutation in one-line notation.
        
    Returns:
        The permutation as a string in cycle notation.

    Example:
        >>> alpha = np.array([2,0,1], dtype=np.intp) # (0,2,1): 0->2, 1->0, 2->1 
        >>> ArrayToCycle(alpha)
        '(0,2,1)'
    """
    unvisited = [True] * len(array)
    cycle = ''
    for i in range(len(array)):
        if unvisited[i]:
            cycle += '('
            cycle += str(i)
            unvisited[i] = False
            j = i
            while unvisited[array[j]]:
                cycle += ','
                j = array[j]
                cycle += str(j)
                unvisited[j] = False
            cycle += ')'
    return cycle