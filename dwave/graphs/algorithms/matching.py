# Copyright 2018 D-Wave Systems Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from collections.abc import Hashable, Iterable, Mapping
from collections import deque

import dimod
from dimod.decorators import graph_argument
from dimod.typing import GraphLike

__all__ = ['maximal_matching',
           'min_maximal_matching',
           'maximum_bipartite_matching',
           ]


@graph_argument('graph')
def maximal_matching(graph: GraphLike,
                     sampler: dimod.Sampler,
                     **sampler_args,
                     ) -> set[Hashable]:
    """Finds an approximate maximal matching.

    Defines a BQM with ground states corresponding to a maximal matching and
    uses the sampler to sample from it.

    A `matching`_ is a subset of edges in which no node occurs more than once.
    A maximal matching is one in which no edges from ``graph`` can be added
    without violating the matching rule.

    Finding maximal matchings can be done is polynomial time, so this method
    is only useful pedagogically.

    Based on the formulation presented in [Luc2014]_.

    Args:
        graph:
            The graph on which to find a maximal matching. Either an integer
            ``n``, interpreted as a complete graph of size ``n``, a nodes/edges
            pair, a list of edges or a NetworkX graph.

        sampler:
            A dimod sampler.

        **sampler_args:
            Additional keyword parameters are passed to the sampler.

    Returns:
        A maximal matching of the graph.

    .. _matching: https://en.wikipedia.org/wiki/Matching_(graph_theory)

    """
    nodes, edges = graph

    if not edges:
        return set()

    bqm = dimod.generators.maximal_matching(graph)
    sampleset = sampler.sample(bqm, **sampler_args)
    sample = sampleset.first.sample

    # the matching are the edges that are 1 in the sample
    return set(tuple(edge) for edge, val in sample.items() if val > 0)


@graph_argument('graph')
def min_maximal_matching(graph: GraphLike,
                         sampler: dimod.Sampler,
                         **sampler_args,
                         ) -> set[Hashable]:
    """Returns an approximate minimum maximal matching.

    Defines a BQM with ground states corresponding to a minimum maximal matching
    and uses the sampler to sample from it.

    A `matching`_ is a subset of edges in which no node occurs more than once.
    A maximal matching is one in which no edges from ``graph`` can be added
    without violating the matching rule. A minimum maximal matching is the
    smallest maximal matching for ``graph``.

    Args:
        graph:
            The graph on which to find a minimum maximal matching. Either an
            integer ``n``, interpreted as a complete graph of size ``n``, a
            nodes/edges pair, a list of edges or a NetworkX graph.

        sampler:
            A dimod sampler.

        **sampler_args:
            Additional keyword parameters are passed to the sampler.

    Returns:
        A minimum maximal matching of the graph.

    Example:
        This example uses a sampler from
        :ref:`index_dimod` to find a minimum maximal
        matching for a Chimera unit cell.

        >>> import dimod
        >>> sampler = dimod.ExactSolver()
        >>> G = dwave.graphs.chimera_graph(1, 1, 4)
        >>> matching = dwave.graphs.min_maximal_matching(G, sampler)

    .. _matching: https://en.wikipedia.org/wiki/Matching_(graph_theory)

    """
    nodes, edges = graph

    if not edges:
        return set()

    bqm = dimod.generators.min_maximal_matching(graph)
    sampleset = sampler.sample(bqm, **sampler_args)
    sample = sampleset.first.sample

    # the matching are the edges that are 1 in the sample
    return set(tuple(edge) for edge, val in sample.items() if val > 0)


def maximum_bipartite_matching(X: Iterable[Hashable],
                               Y: Iterable[Hashable],
                               edges: Mapping[Hashable, Iterable[Hashable]],
                               ) -> Mapping[Hashable, Hashable]:
    """Find one maximum matching in a bipartite graph (Hopcroft-Karp).

    Args:
        X: Iterable of left vertices. Any hashable values work (e.g. ints or
            strings), since vertices are used as dict keys.
        Y: Iterable of right vertices (same hashability requirement as ``X``).
        edges: Mapping from each ``x`` in ``X`` to an iterable of its
            ``Y``-neighbors. Vertices with no edges may be omitted.
            ``edges`` must map vertices in ``X`` to vertices in ``Y``; passing
            keys or neighbors outside these sets is undefined.

    Returns:
        A dict mapping each matched ``x`` to its matched ``y``. Unmatched
        vertices are absent, so ``len(result)`` is the size of the maximum
        matching. If several maximum matchings exist, one of them is
        returned; which one depends on iteration order.

    Notes:
        Uses the Hopcroft-Karp algorithm (O(sqrt(|V|) . |E|)), where 
        |V| = |X| + |Y| is the number of vertices and |E| is the total
        number of edges. See
        <https://en.wikipedia.org/wiki/Hopcroft%E2%80%93Karp_algorithm>

        The augmenting-path search (``dfs``) is recursive, with recursion depth
        bounded by the length of the longest augmenting path in a phase, i.e.
        O(|X| + |Y|) in the worst case. Python's default recursion limit is of
        order of 1000, so inputs where |X| + |Y| is within a few hundred are
        safe.

        This is the same algorithm as `networkx.bipartite.hopcroft_karp_matching`
        in <https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.bipartite.matching.hopcroft_karp_matching.html>
        (except for the greedy warm-start and the BFS shortest-path prune). The
        main advantage of this implementation is for usage in cases where this
        function is called in a hot loop where the inputs are already in the exact
        form this function needs: the two vertex sets are known by construction and
        the edges are already a plain adjacency dict. Using
        `networkx.bipartite.hopcroft_karp_matching` instead would require
        constructing a `nx.Graph` (node/edge insertion, attribute dicts) on every
        call and passing the bipartition we already know as `top_nodes`. In addition,
        `networkx.bipartite.hopcroft_karp_matching` returns a symmetric mapping; when
        a one-directional {left node: right node} map is wanted, that result must be
        stripped. This custom version returns the one-directional map directly.
    """
    pair_x = {x: None for x in X}  # current match of each x (or None)
    pair_y = {y: None for y in Y}  # current match of each y (or None)
    dist = {}  # BFS layer distance per x
    INF = float("inf")

    # Greedy warm-start: before any augmenting-path work, match each free x to
    # any free neighbor y in one linear pass. This seeds the matching so the
    # Hopcroft-Karp phases below start from a large partial matching and have
    # far fewer augmenting phases left to run. It does NOT change the
    # result's cardinality -- Hopcroft-Karp still runs to a maximum matching
    # afterward; only the runtime and the specific pairing chosen may differ.
    for x in X:
        for y in edges.get(x, ()):
            if pair_y[y] is None:  # y still free -> take it
                pair_x[x] = y
                pair_y[y] = x
                break

    def bfs():
        """Layer the graph from free X-vertices; return True if some augmenting
        path reaches a free Y-vertex (another phase can improve)."""
        q = deque()
        for x in X:
            if pair_x[x] is None:  # free x starts at layer 0
                dist[x] = 0
                q.append(x)
            else:
                dist[x] = INF
        dist[None] = INF  # distance to the nearest free y (shortest aug. path)
        while q:
            x = q.popleft()
            if dist[x] < dist[None]:  # prune: don't expand past the shortest layer
                for y in edges.get(x, ()):
                    matched_x = pair_y[y]  # None if y is free
                    if dist[matched_x] == INF:  # free y, or x not yet layered
                        dist[matched_x] = dist[x] + 1
                        q.append(matched_x)
        return dist[None] != INF

    def dfs(x):
        """Try to augment along a shortest layered path starting at x."""
        if x is None:  # reached a free y -> augmenting path complete
            return True
        for y in edges.get(x, ()):
            matched_x = pair_y[y]
            if dist[matched_x] == dist[x] + 1 and dfs(matched_x):
                pair_x[x] = y  # (re)match x--y along the augmenting path
                pair_y[y] = x
                return True
        dist[x] = INF  # dead end: don't revisit this phase
        return False

    while bfs():  # each successful phase adds >= 1 to the matching
        for x in X:
            if pair_x[x] is None:
                dfs(x)

    return {x: y for x, y in pair_x.items() if y is not None}
