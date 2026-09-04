.. _graphs_algorithms:

==========
Algorithms
==========

Implementations of graph-theory algorithms on the D-Wave system and other
binary quadratic model samplers.

.. currentmodule:: dwave.graphs


.. note::
    Some of the algorithms below are implemented by sampling from a binary
    quadratic model. Note that samplers by their nature may not return the
    optimal solution. The functions that use a sampler do not attempt to confirm
    the quality of the returned solution.

.. _graphs_automorphism:

Automorphism
============

An automorphism of a graph is a permutation of its vertices that preserves
adjacency. The set of all automorphisms forms the graph's automorphism group,
which describes its symmetries.

.. automodule:: dwave.graphs.algorithms.automorphism

.. autosummary::
    :toctree: generated/

    schreier_rep
    SchreierContext
    sample_automorphisms
    vertex_orbits
    edge_orbits

.. _graphs_canonicalization:

Canonicalization
================

.. automodule:: dwave.graphs.algorithms.canonicalization

.. autosummary::
    :toctree: generated/

    canonical_chimera_labeling

.. _graphs_clique:

Clique
======

A clique in an undirected graph G = (V, E) is a subset of the vertex set such
that for every two vertices in C there exists an edge connecting the two.

.. figure:: _images/clique.png
    :name: Cover
    :alt: image
    :align: center
    :scale: 40 %

.. automodule:: dwave.graphs.algorithms.clique

.. autosummary::
    :toctree: generated/

    maximum_clique
    clique_number
    is_clique

.. _graphs_coloring:

Coloring
========

Graph coloring is the problem of assigning a color to the vertices of a graph in
a way that no adjacent vertices have the same color.

Example
-------

The map-coloring problem is to assign a color to each region of a map
(represented by a vertex on a graph) such that any two regions sharing a border
(represented by an edge of the graph) have different colors.

.. figure:: _images/Problem_MapColoring.png
    :name: Problem_MapColoringColoring
    :alt: image
    :align: center
    :scale: 70 %

    Coloring a map of Canada with four colors.

.. automodule:: dwave.graphs.algorithms.coloring

.. autosummary::
    :toctree: generated/

    is_vertex_coloring
    min_vertex_coloring
    vertex_coloring
    zephyr_four_color
    pegasus_four_color
    chimera_two_color

.. _graphs_cover:

Cover
=====

Vertex covering is the problem of finding a set of vertices such that all the
edges of the graph are incident to at least one of the vertices in the set.

.. figure:: _images/Cover.png
    :name: CoverCover
    :alt: image
    :align: center
    :scale: 40 %

    Cover for a Chimera unit cell: the nodes of both the blue set of vertices
    (the horizontal tile of the Chimera unit cell) and the red set (vertical
    tile) connect to all 16 edges of the graph.

.. automodule:: dwave.graphs.algorithms.cover

.. autosummary::
    :toctree: generated/

    is_vertex_cover
    min_weighted_vertex_cover
    min_vertex_cover

.. _graphs_elimination_ordering:

Elimination Ordering
====================

Many algorithms for NP-hard problems are exponential in treewidth. However,
finding a lower bound on treewidth is in itself NP-complete. [Gog2004]_
describes a branch-and-bound algorithm for computing the treewidth of an
undirected graph by searching in the space of *perfect elimination ordering* of
vertices of the graph.

A *clique* of a graph is a fully-connected subset of vertices; that is, every
pair of vertices in the clique share an edge. A *simplicial* vertex is one
whose neighborhood induces a clique. A perfect elimination ordering is an
ordering of vertices :math:`1..n` such that any vertex :math:`i` is simplicial
for the subset of vertices :math:`i..n`.

.. automodule:: dwave.graphs.algorithms.elimination_ordering

.. autosummary::
    :toctree: generated/

    chimera_elimination_order
    elimination_order_width
    is_almost_simplicial
    is_simplicial
    max_cardinality_heuristic
    minor_min_width
    min_fill_heuristic
    min_width_heuristic
    pegasus_elimination_order
    treewidth_branch_and_bound

.. _graphs_markov:

Markov Networks
===============

.. automodule:: dwave.graphs.algorithms.markov

.. autosummary::
    :toctree: generated/

    sample_markov_network

.. _graphs_matching:

Matching
========

A matching is a subset of graph edges in which no vertex occurs more than once.

.. figure:: _images/Match.png
    :name: Matching
    :alt: image
    :align: center
    :scale: 40 %

    A matching for a Chimera unit cell: no vertex is incident to more than one
    edge in the set of blue edges

.. automodule:: dwave.graphs.algorithms.matching

.. autosummary::
    :toctree: generated/

    maximal_matching
    min_maximal_matching

.. _graphs_maximum_cut:

Maximum Cut
===========

A maximum cut is a subset of a graph's vertices such that the number of edges
between this subset and the remaining vertices is as large as possible.

.. figure:: _images/MaxCut.png
    :name: Cut
    :alt: image
    :align: center
    :scale: 60 %

    Maximum cut for a Chimera unit cell: the blue line around the subset of
    nodes {4, 5, 6, 7} cuts 16 edges; adding or removing a node decreases the
    number of edges between the two complementary subsets of the graph.

.. automodule:: dwave.graphs.algorithms.max_cut

.. autosummary::
    :toctree: generated/

    maximum_cut
    weighted_maximum_cut

.. _graphs_independent_set:

Independent Set
===============

An independent set is a set of a graph's vertices with no edge connecting any of
its member pairs.

.. figure:: _images/Cover.png
    :name: CoverIndependentSet
    :alt: image
    :align: center
    :scale: 40 %

    Independent sets for a Chimera unit cell: the nodes of both the blue set of
    vertices (the horizontal tile of the Chimera unit cell) and the red set
    (vertical tile) are independent sets of the graph, with no blue node
    adjacent to another blue node and likewise for red nodes.

.. automodule:: dwave.graphs.algorithms.independent_set

.. autosummary::
    :toctree: generated/

    maximum_weighted_independent_set
    maximum_independent_set
    is_independent_set

.. _graphs_partitioning:

Partitioning
============

A `k`-partition consists of `k` disjoint and equally sized subsets of a graph's
vertices such that the total number of edges between nodes in distinct subsets
is as small as possible.

.. figure:: _images/Partitioning.png
    :name: Partition
    :alt: image
    :align: center
    :scale: 60 %

    A 2-partition for a simple graph: the nodes in blue are in the '0' subset,
    and the nodes in red are in the '1' subset. There are no other arrangements
    with fewer edges between two equally sized subsets.

.. automodule:: dwave.graphs.algorithms.partition

.. autosummary::
    :toctree: generated/

    partition

.. _graphs_social:

Social
======

A signed social network graph is a graph whose signed edges represent
friendly/hostile interactions between vertices.

.. figure:: _images/Social.png
    :name: Social
    :alt: image
    :align: center
    :scale: 80 %

    A signed social graph for three nodes, where Eve and Bob are friendly with
    each other and hostile to Alice. This network is balanced because it can be
    cleanly divided into two subsets, {Bob, Eve} and {Alice}, with friendly
    relations within each subset and only hostile relations between the subsets.

.. automodule:: dwave.graphs.algorithms.social

.. autosummary::
    :toctree: generated/

    structural_imbalance

.. _graphs_traveling_salesperson:

Traveling Salesperson
=====================

A traveling salesperson route is an ordering of the vertices in a complete
weighted graph.

.. figure:: _images/tsp.png
    :name: TSP_route
    :alt: image
    :align: center
    :scale: 80 %

    A traveling salesperson route of [2, 1, 0, 3].

.. automodule:: dwave.graphs.algorithms.tsp

.. autosummary::
    :toctree: generated/

    traveling_salesperson
    is_hamiltonian_path
