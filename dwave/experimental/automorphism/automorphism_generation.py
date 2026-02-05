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

from collections import deque
from collections.abc import Hashable
from dataclasses import dataclass
from enum import Enum, auto
import hashlib
from itertools import chain
import random
from typing import Mapping

import networkx as nx
import numpy as np
from numpy.typing import NDArray

@dataclass
class ComponentInfo:
    """Container for per-component data used during automorphism discovery on disjoint graphs."""
    u_vector: list
    nodes: NDArray
    best_perm: NDArray

class EnterMode(Enum):
    """Controls when the ``_enter()`` function attempts to compose new automorphisms."""
    RECURSE = auto()
    RECURSE_ONCE = auto()
    NO_RECURSE = auto()

class SchreierContext:
    """This object holds mutable states used throughout the automorphism calculation.

    Args:
        graph: A NetworkX Graph object representing the input graph.
        num_samples: Number of samples to use for generating new coset representatives
            from the existing set. If not provided, all coset representatives are used.
        seed: Seed used for reproducibility. Defaults to 42.
    """
    def __init__(self, graph: nx.Graph, num_samples: int | None = None, seed: int = 42) -> None:
        original_nodes_sorted = sorted(graph.nodes())
        self._index_to_node: dict[int, Hashable] = {
            new: old for new, old in enumerate(original_nodes_sorted)
        }
        self._node_to_index: dict[Hashable, int] = {
            old: new for new, old in enumerate(original_nodes_sorted)
        }
        graph = nx.relabel_nodes(graph, self._node_to_index)  # relabel nodes contiguously (0...n-1)

        self._nodes: list[int] = list(graph.nodes())
        self._num_nodes: int = graph.number_of_nodes()
        self._graph_edges: list[tuple[int, int]] = list(graph.edges())
        self._neighbours: list[set[int]] = [set(graph.neighbors(i)) for i in range(self._num_nodes)]
        self._graph: nx.Graph = graph

        self._num_samples: int | None = num_samples
        self._rng: random.Random = random.Random(seed)

        self._leaf_nodes: int = 0
        self._nodes_reached: int = 0
        self._depth: int = 0

        self._u_map: dict[np.intp, int] = {}
        self._u_len: int = 0
        self._u_vector: list = []
        self._u_vector_inv: list[list[NDArray[np.intp]]] = []

        self._identity: NDArray[np.intp] = np.arange(self._num_nodes, dtype=np.intp)

        self._best_perm: NDArray = np.arange(self._num_nodes)
        self._best_perm_exist: bool = False
        self._compare_adj: bool = False
        self._trace_history: list = []

        self._in_colors_adj: bytearray = bytearray(self._num_nodes)
        self._in_refine_stack: bytearray = bytearray(self._num_nodes)

        self._color_degree: list[int] = [0] * self._num_nodes
        self._min_color_degree: list[int] = [0] * self._num_nodes
        self._max_color_degree: list[int] = [0] * self._num_nodes
        self._active_vertices: list[list[int]] = [[] for _ in range(self._num_nodes)]

        if self._num_nodes <= 65535:
            self._color_dtype: np.dtype = np.uint16
        else:
            self._color_dtype: np.dtype = np.uint32

    @property
    def leaf_nodes(self) -> int:
        """Number of leaf nodes encountered in the search tree."""
        return self._leaf_nodes

    @property
    def nodes_reached(self) -> int:
        """Total number of nodes reached during traversal of the search tree."""
        return self._nodes_reached

    @property
    def index_to_node(self) -> dict[int, Hashable]:
        """The mapping from the basis of relabelled nodes (0...n-1) to the original
        node labels."""
        return self._index_to_node

    @property
    def node_to_index(self) -> dict[Hashable, int]:
        """The mapping from the original node labels to the basis of relabelled
        nodes (0...n-1)."""
        return self._node_to_index

    @property
    def u_map(self) -> dict[np.intp, int]:
        """Map from coset representative group index to stabilizer index."""
        return self._u_map

    @property
    def u_vector(self) -> list[list[NDArray[np.intp]]]:
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
    def vertex_orbits(self) -> list[list[int]]:
        """Vertex orbits induced by the coset representatives in u_vector and returned
        in the basis of relabelled nodes (0...n-1)."""
        return vertex_orbits(self._u_vector, self._nodes)

    @property
    def vertex_orbits_original_labels(self) -> list[list[Hashable]]:
        """Vertex orbits induced by the coset representatives in u_vector and returned
        with the original node labels."""
        return vertex_orbits(self._u_vector, self._nodes, index_to_node=self._index_to_node)

    @property
    def edge_orbits(self) -> list[list[int]]:
        """Edge orbits induced by the coset representatives in u_vector and returned
        in the basis of relabelled nodes (0...n-1)."""
        return edge_orbits(self._u_vector, self._graph_edges)

    @property
    def edge_orbits_original_labels(self) -> list[list[Hashable]]:
        """Edge orbits induced by the coset representatives in u_vector and returned
        with the original node labels."""
        return edge_orbits(self._u_vector, self._graph_edges, index_to_node=self._index_to_node)

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
        mask = (g != self._identity)
        index = mask.argmax()
        next_diff = 0

        while mask[index]:
            next_diff += index
            if next_diff not in self._u_map:
                return next_diff, g

            for i, h in enumerate(self._u_vector[self._u_map[next_diff]]):
                if h[next_diff] == g[next_diff]:
                    break
            else:
                return next_diff, g

            g = self._u_vector_inv[self._u_map[next_diff]][i][g]
            mask = (g[next_diff:] != self._identity[next_diff:])
            index = mask.argmax()

        return self._num_nodes, g

    def _enter(self, g: NDArray[np.intp], mode: EnterMode = EnterMode.RECURSE) -> None:
        """Add automorphism if it can't be composed from coset representatives.

        Based on Algorithm 6.11 from Kreher, D. L., & Stinson, D. R. (1999).
        Combinatorial algorithms: Generation, enumeration, and search.

        If an automorphism can't be composed from existing coset representatives
        it is added as a new coset representative to u_vector. Depending on the 
        setting of ``mode``, ``_enter()`` is called recursively to attempt to
        compose additional coset representatives from the composition between
        the newly-discovered coset representative and existing coset representatives.

        The automorphisms discovered will result in pruning comparable to nauty,
        as measured by comparing the total number of search tree nodes visited
        for zephyr graphs of various sizes.

        Args:
            g: A permutation represented as a list of integers in one-line notation.
            mode: Specifies if recursive calls to ``enter()`` are performed to attempt
                to compose new automorphisms. The setting ``EnterMode.RECURSE_ONCE``
                results in a single call to ``enter()`` per coset representative where
                no further attempts to compose automorphisms occur. 
        """
        i, g = self._test_composability(g)
        if i == self._num_nodes:
            return

        if i not in self._u_map:
            self._u_map[i] = self._u_len
            self._u_len += 1
            self._u_vector.append([])
            self._u_vector_inv.append([])

        self._u_vector[self._u_map[i]].append(g)
        self._u_vector_inv[self._u_map[i]].append(inv(self._num_nodes, g))

        if mode is EnterMode.NO_RECURSE:
            return

        for u_i in self._u_vector:
            for h in u_i:
                f = mult(g, h)
                if mode is EnterMode.RECURSE_ONCE:
                    self._enter(f, mode=EnterMode.NO_RECURSE)
                else:
                    self._enter(f)

    def _refine(
        self,
        partition: list[set[int]],
        trace: NDArray[np.integer],
        color: NDArray[np.integer],
        num_colors: int,
        individualized_vertex: int | None = None,
    ) -> None:
        """Perform color refinement on the current partition until an equitable
        coloring is reached.

        This procedure implements the 1-dimensional Weisfeiler-Leman (WL) refinement,
        following Algorithms 2 and 3 of Berkholz (2016), *Tight lower and upper bounds
        for the complexity of canonical color refinement*.

        A refinement stack is initialized with either:
            • all color classes (if no vertex has been individualized), or
            • the color class of the individualized vertex.

        For each color class popped from the stack, the algorithm computes the
        color-degree of every vertex: the number of neighbours it has in the refining
        color class. These color-degrees determine how each color class should be
        split. If a color class contains vertices with differing color-degrees, it is
        partitioned into new color classes, and the smaller subcells are pushed onto
        the refinement stack.

        The process continues until no color class can be further refined, yielding an
        equitable coloring.

        If a vertex was individualized prior to this refinement step, only the
        color class containing that vertex needs to be placed on the refinement
        stack initially, since only colors adjacent to that color can be affected.

        For performance reasons, ``num_colors`` is passed as a single-element list
        so that updates to the number of colors persist across calls without having
        to return anything.

        Args:
            partition: The current partition structure, represented as a list of sets of vertices 
                ordered by color.
            trace: A list of the sizes of each partition cell (color class), ordered by color.
            color: An array mapping each vertex to its current color.
            num_colors: The current number of colors in the partition.
            individualized_vertex: The vertex individualized prior to this refinement step, if any.

        Returns:
            The new number of colors, the updated trace array, and the updated color array.
        """
        neighbours = self._neighbours
        color_degree = self._color_degree
        min_color_degree = self._min_color_degree
        max_color_degree = self._max_color_degree
        active_vertices = self._active_vertices
        in_refine_stack = self._in_refine_stack
        in_colors_adj = self._in_colors_adj

        colors_adj = []

        if individualized_vertex is None:
            refine_stack = list(range(num_colors))
        else:
            refine_stack = [color[individualized_vertex]]
        num_colors = [num_colors] # mutable container so ``_split_up_color()`` can increment it

        for v in refine_stack:
            in_refine_stack[v] = 1

        while refine_stack:
            refinement_color = refine_stack.pop()
            in_refine_stack[refinement_color] = 0

            for v in partition[refinement_color]:
                for w in neighbours[v]:
                    color_degree[w] += 1
                    cw = color[w]
                    if color_degree[w] == 1:
                        active_vertices[cw].append(w)
                    if in_colors_adj[cw] == 0:
                        colors_adj.append(cw)
                        in_colors_adj[cw] = 1
                    if color_degree[w] > max_color_degree[cw]:
                        max_color_degree[cw] = color_degree[w]

            for c in colors_adj:
                if trace[c] != len(active_vertices[c]):
                    min_color_degree[c] = 0
                else:
                    min_color_degree[c] = max_color_degree[c]
                    for v in active_vertices[c]:
                        if color_degree[v] < min_color_degree[c]:
                            min_color_degree[c] = color_degree[v]

            colors_to_split = []
            for c in colors_adj:
                if min_color_degree[c] < max_color_degree[c]:
                    colors_to_split.append(c)

            for color_to_split in sorted(colors_to_split):
                self._split_up_color(
                    color_to_split=color_to_split,
                    partition=partition,
                    color=color,
                    trace=trace,
                    active_vertices=active_vertices,
                    color_degree=color_degree,
                    min_degree=min_color_degree[color_to_split],
                    max_degree=max_color_degree[color_to_split],
                    refine_stack=refine_stack,
                    in_refine_stack=in_refine_stack,
                    num_colors=num_colors,
                )

            ## reset attributes
            for c in colors_adj:
                for v in active_vertices[c]:
                    color_degree[v] = 0
                max_color_degree[c] = 0
                active_vertices[c] = []
                in_colors_adj[c] = 0
            colors_adj = []

        return num_colors[0], trace, color

    def _split_up_color(
        self,
        *,
        color_to_split: int,
        partition: list[set[int]],
        color: NDArray[np.integer],
        trace: NDArray[np.integer],
        active_vertices: list[list[int]],
        color_degree: list[int],
        min_degree: int,
        max_degree: int,
        refine_stack: list[int],
        in_refine_stack: bytearray,
        num_colors: list[int],
    ) -> None:
        """Splits a color class into subcells based on the color-degrees of its vertices.

        Based on algorithm 3 of Berkholz (2016), *Tight lower and upper bounds
        for the complexity of canonical color refinement*.

        Given a color class ``color_to_split`` whose vertices exhibit differing
        color-degrees with respect to the current refining color, this routine
        partitions that class into new color classes. Vertices with the same
        color-degree remain together, while vertices with different degrees are
        assigned fresh color identifiers.

        The largest resulting subcell retains the original color label, while
        all smaller subcells are assigned new colors and pushed onto the
        refinement stack (Hopcroft's trick). The partition structure, trace array,
        number of colors, and vertex-to-color mapping are updated in place.

        Args:
            color_to_split: The color class to be split.
            partition: The current partition structure, represented as a list of sets of vertices 
                ordered by color.
            color: An array mapping each vertex to its current color.
            trace: A list of the sizes of each partition cell (color class), ordered by color.
            active_vertices: Lists of vertices adjacent to the color class being split,
                ordered by color.
            color_degree: The color-degree of each vertex.
            min_degree: Minimum color-degree among vertices in the color class being split.
            max_degree: Maximum color-degree among vertices in the color class being split.
            refine_stack: Stack of colors scheduled for refinement.
            in_refine_stack: Flags indicating which colors are already on the stack.
            num_colors: The number of colors, used to determine the next color label to assign to
                newly-refined cells. Stored as a single-element list so that updates persist across
                calls.
        """
        degree_to_new_color = [0] * (max_degree + 1)
        num_color_degree = [0] * (max_degree + 1)
        num_color_degree[0] = trace[color_to_split] - len(active_vertices[color_to_split])

        for v in active_vertices[color_to_split]:
            num_color_degree[color_degree[v]] += 1

        largest_subcell_degree = 0
        for i in range(1, max_degree + 1):
            if num_color_degree[i] > num_color_degree[largest_subcell_degree]:
                largest_subcell_degree = i

        for i in range(max_degree + 1):
            if num_color_degree[i] > 0:
                if i == min_degree:
                    degree_to_new_color[i] = color_to_split
                    if not in_refine_stack[color_to_split] and i != largest_subcell_degree:
                        refine_stack.append(degree_to_new_color[i])
                        in_refine_stack[degree_to_new_color[i]] = 1
                else:
                    degree_to_new_color[i] = num_colors[0]
                    partition[num_colors[0]] = set()
                    if in_refine_stack[color_to_split] or i != largest_subcell_degree:
                        refine_stack.append(degree_to_new_color[i])
                        in_refine_stack[degree_to_new_color[i]] = 1
                    num_colors[0] += 1

        for v in active_vertices[color_to_split]:
            new_color = degree_to_new_color[color_degree[v]]
            if new_color != color_to_split:
                partition[color_to_split] = partition[color_to_split] - {v} # must create new obj
                partition[new_color].add(v)
                trace[color_to_split] -= 1
                trace[new_color] += 1
                color[v] = new_color

    def _canon(
        self,
        partition: list[set[int]],
        trace: NDArray[np.integer],
        color: NDArray[np.integer],
        num_colors: int,
        individualized_vertex: int | None = None,
    ) -> None:
        """Generate search tree based on iterative color refinement and vertex
        individualization.

        Loosely based on Algorithm 7.9 from Kreher, D. L., & Stinson, D. R. (1999).
        Combinatorial algorithms: Generation, enumeration, and search. Additional
        data structures are used to efficiently track the number of vertices
        belonging to each color, vertex colors, and number of colors. Additionally,
        the most recently individualized vertex is tracked and used to perform
        color refinement more efficiently.

        Color refinement is performed iteratively on a graph until a discrete
        coloring is achieved. If the coloring is not discrete after refinement,
        vertices belonging to the same color are individualized, meaning that they
        are assigned a new color, often breaking the symmetry of the graph and
        allowing a subsequent color refinement step to produce further refinement.

        By default, graph comparisons using adjacency matrices are not performed, as
        this becomes a bottleneck for even modestly sized graphs. Instead, the
        ``trace`` for each graph is compared, which corresponds to the number of
        vertices belonging to each color, ordered by color. This check is orders of
        magnitude faster and has been found to have identical pruning capability
        for graphs of interest, such as chimera, pegasus, and zephyr graphs, as
        well as the disjoint compositions of smaller and simpler graphs as may
        be encountered when doing parallel embeddings.

        If a graph has more than one component, comparisons using adjacency matrices are
        used. This enables isomorphism detection between components, and in turn
        a more efficient approach to generating the full automorphism group, which
        may contain many automorphisms between isomorphic components. 

        Kreher and Stinson perform comprehensive pruning by changing the base of
        the left transversals to coincide with the current permutation order up to the
        first non-discrete partition cell, or first split. At the cost of performing
        this base change, it allows pruning to be performed by only considering
        the left transversal with a stabilizer index equal to the index of the first
        split. In practice, changing the base at each node of the search tree
        becomes prohibitively expensive even more mostly sized graphs, and instead
        the approach taken here is to avoid base changes, but instead to more carefully
        evaluate which coset representatives to use for pruning. This is done by
        ignoring the automorphisms that do not respect the current partition structure. 

        Args:
            partition: The current partition structure, represented as a list of
                sets of vertices ordered by color.
            trace: The number of vertices belonging to each color, ordered by color.
            color: A map from each vertex to its color.
            num_colors: The number of unique colors, equivalent to the number
                of cells in the partition.
            individualized_vertex: The most recently individualized vertex.
        """
        self._nodes_reached += 1
        self._depth += 1

        num_colors, trace, color = self._refine(
            partition,
            trace,
            color,
            num_colors,
            individualized_vertex=individualized_vertex
        )

        if not self._best_perm_exist:
            self._trace_history.append(trace.tobytes())

        # first non-singleton block index
        first_split = self._num_nodes - 1
        for i, block in enumerate(partition):
            if len(block) > 1:
                first_split = i
                break

        compare_result = 2
        if self._best_perm_exist: # if a leaf node has been reached previously

            if self._compare_adj:
                perm_candidate = list(chain.from_iterable(p for p in partition if p is not None))
                compare_result = self._compare(perm_candidate, first_split)
            else:
                compare_result = trace.tobytes() == self._trace_history[self._depth - 1]

            if compare_result == 0:
                return

        if first_split == self._num_nodes - 1: # leaf node reached
            self._leaf_nodes += 1

            if not self._best_perm_exist:
                self._best_perm_exist = True
                self._best_perm[:] = list(chain.from_iterable(partition))

            elif compare_result == 2:
                perm_candidate = list(chain.from_iterable(partition))
                self._best_perm[:] = perm_candidate

            elif compare_result == 1:
                perm_transformed = np.empty(self._num_nodes, dtype=np.intp)
                perm_candidate = list(chain.from_iterable(partition))
                perm_transformed[perm_candidate] = self._best_perm
                self._enter(perm_transformed)

            return

        candidates = sorted(partition[first_split])
        remaining_in_block = partition[first_split]
        updated_partition = partition
        trace[first_split] -= 1
        trace[num_colors] = 1

        while candidates:
            vertex = next(iter(candidates))
            updated_partition[first_split] = remaining_in_block - {vertex}
            updated_partition[num_colors] = {vertex}
            individualized_partition = list(updated_partition) # copy outer list
            color[vertex] = num_colors # updated individualized cell
            trace_copy = np.array(trace)
            color_copy = np.array(color)

            self._canon(
                individualized_partition,
                trace_copy,
                color_copy,
                num_colors + 1,
                individualized_vertex=vertex
            )

            color[vertex] = first_split
            candidates.remove(vertex)

            # prune the search tree using automorphisms
            for stab_index, u_index in self._u_map.items():
                if stab_index > vertex: # these automorphisms map vertex to itself
                    continue

                for g in self._u_vector[u_index]:
                    if g[vertex] not in candidates:
                        continue

                    # automorphism must respect current partition structure
                    for w in candidates:
                        if color[w] != color[g[w]]:
                            break
                    else:
                        candidates.remove(g[vertex])

            self._depth -= 1

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

    def _certificate(self) -> bytes:
        """Generate a canonical certificate for a graph.

        Based on the permutation ``self.best_perm`` that minimizes the binary value
        of the upper triangular portion of the adjacency matrix of the graph,
        as found by comparing leaf nodes of the search tree during the search for
        automorphisms.

        Returns:
            cert_hash: a hash object of the canonical adjacency bitstring.
        """
        cert_hash = hashlib.sha256()
        neighbours = self._neighbours
        best_perm = self._best_perm

        for j in range(1, self._num_nodes):
            neighbours_best_j = neighbours[best_perm[j]]

            for i in range(j):
                bit = 1 if best_perm[i] in neighbours_best_j else 0
                cert_hash.update(bytes([bit]))

        return cert_hash.digest()

    def _initial_partition(self) -> tuple[list[set[int] | None], np.ndarray, np.ndarray, int]:
        """Initialize the initial partition for a graph.

        Currently this only supports graphs whose vertices are initially the same
        color, but could be expanded in the future to accommodate graphs with a
        non-trivial initial vertex coloring.

        Returns:
            partition: The initial partition structure, represented as a list of sets of vertices 
                ordered by color.
            trace: A list of the sizes of each partition cell (color class), ordered by color.
            color: An array mapping each vertex to its current color.
            num_colors: The number of colors in the initial partition.
        """
        partition = [set(self._nodes)] + [None] * (self._num_nodes - 1)
        trace = np.zeros(self._num_nodes, dtype=self._color_dtype)
        trace[0] = self._num_nodes
        color = np.zeros(self._num_nodes, dtype=self._color_dtype)
        num_colors = 1

        return partition, trace, color, num_colors


def vertex_orbits(
    u_vector: list[list[NDArray[np.intp]]],
    nodes: list[int],
    index_to_node: Mapping[int, int] | None = None,
) -> list[list[int]]:
    """Calculate vertex orbits using breadth-first search.

    If ``u_vector`` contains no coset representatives, trivial orbits are returned.

    Args:
        u_vector: Coset representatives grouped by stabilizer index.
        nodes: List of vertex indices used to return trivial orbits when ``u_vector`` is empty.
        index_to_node: An optional dictionary for returning orbits with their original node labels.

    Returns:
        A list of orbits, each orbit is a list of vertex indices.

    Example:
        >>> import numpy as np
        >>> from dwave.experimental.automorphism import vertex_orbits
        ...
        >>> u_vector = [
        ...     [np.array([0, 1, 4, 3, 2, 6, 5, 7])],
        ...     [np.array([2, 1, 4, 3, 0, 7, 5, 6]), np.array([4, 1, 0, 3, 2, 6, 7, 5])],
        ...     [np.array([0, 3, 2, 1, 4, 5, 6, 7])],
        ... ]
        >>> nodes = list(range(8))
        >>> vertex_orbits(u_vector, nodes)
        [[0, 2, 4], [1, 3], [5, 6, 7]]
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
    label = (lambda x: index_to_node[x]) if index_to_node is not None else int

    for v_start in nodes:
        if v_start in visited:
            continue

        visited.add(v_start)
        orb = [label(v_start)]

        q = deque([v_start])
        while q:
            v_current = q.popleft()

            for g in generators:
                v_current = g[v_current]
                if v_current not in visited:
                    visited.add(v_current)
                    q.append(v_current)
                    orb.append(label(v_current))
        orb.sort()
        orbits.append(orb)

    orbits.sort()
    return orbits


def edge_orbits(
    u_vector: list[list[NDArray[np.intp]]],
    edges: list[tuple[int, int]],
    index_to_node: Mapping[int, int] | None = None,
) -> list[list[int]]:
    """Calculate edge orbits using breadth-first search.

    Args:
        u_vector: Coset representatives grouped by stabilizer index.
        edges: List of graph edges as tuples of vertex index pairs.

    Returns:
        A list of orbits, each orbit is a list of edges (tuples of vertex index pairs).

    Example:
        >>> import numpy as np
        >>> from dwave.experimental.automorphism import edge_orbits
        ...
        >>> u_vector = [
        ...     [np.array([0, 1, 4, 3, 2, 6, 5, 7])],
        ...     [np.array([2, 1, 4, 3, 0, 7, 5, 6]), np.array([4, 1, 0, 3, 2, 6, 7, 5])],
        ...     [np.array([0, 3, 2, 1, 4, 5, 6, 7])],
        ... ]
        >>> edges = [
        ...     (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6),
        ...     (6, 7), (7, 0), (0, 3), (1, 4), (2, 6), (5, 7)
        ... ]
        >>> orbits = edge_orbits(u_vector, edges)
        >>> orbits[0]
        [(0, 1), (0, 3), (1, 2), (1, 4), (2, 3), (3, 4)]
        >>> orbits[1:]
        [[(0, 7), (2, 6), (4, 5)], [(5, 6), (5, 7), (6, 7)]]
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
    label = (lambda x: index_to_node[x]) if index_to_node is not None else int

    for u_start, v_start in edges:
        e_start = (u_start, v_start) if u_start < v_start else (v_start, u_start)

        if e_start in visited:
            continue

        visited.add(e_start)
        orb = [tuple(label(x) for x in e_start)]

        q = deque([e_start])
        while q:
            u, v = q.popleft()
            for g in generators:
                e_current = (g[u], g[v]) if g[u] < g[v] else (g[v], g[u])

                if e_current not in visited:
                    visited.add(e_current)
                    q.append(e_current)
                    orb.append(tuple(label(x) for x in e_current))

        orb.sort()
        orbits.append(orb)

    orbits.sort()
    return orbits


def sample_automorphisms(
    u_vector: list[list[NDArray[np.intp]]],
    num_samples: int = 1,
    seed: int | None = None,
) -> list[NDArray[np.intp]]:
    """Uniformly sample automorphisms from the Schreier-Sims representation.

    Randomly samples one coset representative from each non-trivial left
    transversal and takes the product, guaranteeing uniform sampling. The
    automorphisms can be composed uniformly regardless of the ordering of
    the left transversals in 'u_vector'. All products involving identity
    automorphisms are ignored.

    Args:
        u_vector: Coset representatives grouped by stabilizer index.
        num_samples: The number of automorphisms to return.
        seed: Random seed for reproducibility.

    Returns:
        A list of uniformly sampled automorphisms in one-line notation.

    Example:
        >>> import networkx as nx
        >>> from dwave.experimental.automorphism import schreier_rep, sample_automorphisms
        ...
        >>> graph = nx.cycle_graph(8)
        >>> result = schreier_rep(graph)
        >>> sample_automorphisms(result.u_vector, seed=42)
        [array([3, 4, 5, 6, 7, 0, 1, 2])]
        >>> sample_automorphisms(result.u_vector, num_samples=2, seed=42)
        [array([3, 4, 5, 6, 7, 0, 1, 2]), array([6, 5, 4, 3, 2, 1, 0, 7])]
    """
    rng = np.random.default_rng(seed)
    num_nodes = len(u_vector[0][0])
    u_counts = [len(u_i) for u_i in u_vector]
    sampled_automorphisms = []

    for _ in range(num_samples):
        sample_indices = rng.integers(low=-1, high=u_counts)
        g_product = np.arange(num_nodes)

        for i, u_i in enumerate(u_vector):
            if sample_indices[i] >= 0:
                g = u_i[sample_indices[i]]
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
        >>> import numpy as np
        >>> from dwave.experimental.automorphism import mult
        ...
        >>> alpha = np.array([2,0,1], dtype=np.intp) # (0,2,1): 0->2, 1->0, 2->1
        >>> beta  = np.array([1,2,0], dtype=np.intp) # (0,1,2): 0->1, 1->2, 2->0
        >>> mult(alpha, beta)
        array([0, 1, 2])
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
        >>> import numpy as np
        >>> from dwave.experimental.automorphism import inv
        ...
        >>> alpha = np.array([2,0,1], dtype=np.intp) # (0,2,1): 0->2, 1->0, 2->1
        >>> inv(3, alpha)
        array([1, 2, 0])
    """
    alpha_inv = np.empty(n, dtype=np.intp)
    alpha_inv[alpha] = np.arange(n, dtype=alpha_inv.dtype)
    return alpha_inv


def schreier_rep(
    graph: nx.Graph,
    num_samples: int | None = None,
    seed: int = 42,
) -> SchreierContext:
    """Compute Schreier representatives and orbits for a graph.

    Builds a depth-first search tree, iteratively performing color refinement
    and vertex individualization until leaf nodes are reached where all graph
    vertices are uniquely colored. Leaf nodes with identical adjacency matrices
    represent graph automorphisms. Discovered automorphisms are used to prune
    the search tree.

    If graphs have more than one component, automorphisms are found for each
    individual component, and automorphisms between components are determined
    by considering which components are isomorphic. Since the number of automorphisms
    between isomorphic components scales factorially with the number of components,
    this is significantly faster than naively performing refinement-individualization
    over the whole graph. It would be possible to update ``u_vector`` directly
    without using ``enter()``, which in principle should be even faster, and should
    be the first place to look if further performance improvements are required.

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
    if nx.number_connected_components(graph) == 1:
        ctx = SchreierContext(graph, num_samples=num_samples, seed=seed)
        initial_partition, trace, color, num_colors = ctx._initial_partition()
        ctx._canon(initial_partition, trace, color, num_colors)
        return ctx

    # relabel vertices so components have contiguous labels
    index_to_node = {}
    node_to_index = {}
    next_label = 0

    component_vertices = list(nx.connected_components(graph))
    for vertices in component_vertices:
        for vertex in sorted(vertices):
            node_to_index[vertex] = next_label
            index_to_node[next_label] = vertex
            next_label += 1

    graph = nx.relabel_nodes(graph, node_to_index, copy=True)

    # enter component automorphisms into global graph
    ctx = SchreierContext(graph, num_samples=num_samples, seed=seed)
    ctx._index_to_node = index_to_node
    ctx._node_to_index = node_to_index

    # group isomorphic components together
    components = [ctx._graph.subgraph(c).copy() for c in nx.connected_components(ctx._graph)]

    unique_components = {}
    for comp in components:
        ctx_comp = SchreierContext(comp, num_samples=num_samples, seed=seed)
        ctx_comp._compare_adj = True

        initial_partition, trace, color, num_colors = ctx_comp._initial_partition()
        ctx_comp._canon(initial_partition, trace, color, num_colors)

        ctx._nodes_reached += ctx_comp.nodes_reached # update the global search tree statistics
        ctx._leaf_nodes += ctx_comp.leaf_nodes

        unique_components.setdefault(ctx_comp._certificate(), []).append(
            ComponentInfo(ctx_comp._u_vector, np.array(sorted(comp.nodes())), ctx_comp._best_perm)
        )

    # enter the local automorphisms
    graph_nnodes = ctx._graph.number_of_nodes()
    for identical_components in unique_components.values():
        for comp in identical_components:
            for u in chain.from_iterable(comp.u_vector):
                u_global = np.arange(graph_nnodes)
                u_global[comp.nodes] = u_global[comp.nodes][u]
                ctx._enter(u_global, mode=EnterMode.NO_RECURSE)

    # enter swap automorphisms
    for comps in unique_components.values():
        for i in range(len(comps) - 1):
            i_nodes = comps[i].nodes
            j_nodes = comps[i + 1].nodes

            # swap automorphisms must be entered in the canonical basis
            i_canon_perm = comps[i].best_perm
            j_canon_perm = comps[i + 1].best_perm
            i_canon = i_nodes[i_canon_perm]
            j_canon = j_nodes[j_canon_perm]

            u_global = np.arange(graph_nnodes)
            u_global[i_canon], u_global[j_canon] = u_global[j_canon], u_global[i_canon]
            ctx._enter(u_global, mode=EnterMode.RECURSE_ONCE)

    return ctx

def array_to_cycle(
    array: NDArray[np.intp],
    index_to_node: Mapping[int, Hashable] | None = None
) -> str:
    """Convert an array in one-line notation to a string in cycle notation.

    Based on Algorithm 6.4 from Kreher, D. L., & Stinson, D. R. (1999).
    Combinatorial algorithms: Generation, enumeration, and search.

    Args:
        array: The permutation in one-line notation.
        index_to_node: An optional relabelling dictionary. By default, array indices
            are used.

    Returns:
        The permutation as a string in cycle notation.

    Example:
        >>> import numpy as np
        >>> from dwave.experimental.automorphism import array_to_cycle
        ...
        >>> alpha = np.array([2,0,1], dtype=np.intp) # (0,2,1): 0->2, 1->0, 2->1
        >>> array_to_cycle(alpha)
        '(0,2,1)'
        >>> array_to_cycle(np.array([2,0,1]), index_to_node={0: 5, 1: 7, 2: 9})
        '(5,9,7)'
    """
    if index_to_node is not None:
        expected = set(range(len(array)))
        if index_to_node.keys() != expected:
            missing = expected - index_to_node.keys()
            raise ValueError(f"index_to_node missing keys: {missing}")

    label = (lambda x: str(index_to_node[x])) if index_to_node is not None else str
    unvisited = [True] * len(array)
    cycle_parts = []

    for i in range(len(array)):
        if unvisited[i]:
            cycle_parts.append('(')
            cycle_parts.append(label(i))
            unvisited[i] = False
            j = i

            while unvisited[array[j]]:
                cycle_parts.append(',')
                j = array[j]
                cycle_parts.append(label(j))
                unvisited[j] = False

            cycle_parts.append(')')
    return ''.join(cycle_parts)
