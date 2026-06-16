:warning: *dwave-networkx* is deprecated in favor of *dwave-graphs*. The initial
    release of dwave-graphs includes most functionality previously provided by
    dwave-networkx, now available under the new namespace, ``dwave.graphs``.

.. image:: https://img.shields.io/pypi/v/dwave-networkx.svg
    :target: https://pypi.org/project/dwave-networkx

.. image:: https://circleci.com/gh/dwavesystems/dwave-graphs.svg?style=shield&branch=legacy/dwave-networkx
    :target: https://circleci.com/gh/dwavesystems/dwave-networkx

==============
dwave-networkx
==============

.. start_dnx_about

dwave-networkx is an extension of `NetworkX <https://networkx.org>`_\ ---a
Python language package for exploration and analysis of networks and network
algorithms---for users of D-Wave quantum computers. It provides tools for
working with quantum processing unit (QPU) topology graphs, such as the Pegasus
used on the Advantage\ :sup:`TM` quantum computer, and implementations of
graph-theory algorithms on D-Wave quantum computers and other binary quadratic
model (BQM) samplers.

This example generates a Pegasus graph of the size used by Advantage QPUs.

>>> import dwave_networkx as dnx
>>> graph = dnx.pegasus_graph(16)

.. end_dnx_about

Installation
============

**Installation from PyPi:**

.. code-block:: bash

    pip install dwave_networkx

**Installation from source:**

.. code-block:: bash

    pip install -r requirements.txt
    python setup.py install

License
=======

Released under the Apache License 2.0.

Contributing
============

Ocean's `contributing guide <https://docs.dwavequantum.com/en/latest/ocean/contribute.html>`_
has guidelines for contributing to Ocean packages.
