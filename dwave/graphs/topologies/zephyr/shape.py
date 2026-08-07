# Copyright 2026 D-Wave
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


from __future__ import annotations

from dwave.graphs.topologies.common.shape import TopologyShape, _Infinite, _Quotient

__all__ = ["ZephyrShape"]


class ZephyrShape(TopologyShape):
    """A class to represent the shape parmaters associated with a Zephyr graph.

    Args:
        m: The grid size of the graph. Defaults to ``INFINITE``.
        t: The tile size of the graph. Defaults to ``QUOTIENT``.
        check_shape_valid: Flag to whether to check the parameters
            are valid on instantiation. Defaults to ``True``.
    """

    topology_name = "zephyr"

    def __init__(
        self,
        m: int | _Infinite = _Infinite.INFINITE,
        t: int | _Quotient = _Quotient.QUOTIENT,
        check_shape_valid: bool = True,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(m, t, check_shape_valid, *args, **kwargs)

    def _args_are_valid(self, m: int | _Infinite, t: int | _Quotient, *args, **kwargs) -> None:
        """Checks whether the given parameters are valid for a Zephyr shape.

        Args:
            m: The grid size of Zephyr graph.
            t: The tile size of Zephyr graph.
        Raises:
            ValueError: If m is not ``_Infinite.INFINITE`` and is non-positive.
            ValueError: If t is not ``_Quotient.QUOTIENT`` and is non-positive.
        """
        if not isinstance(m, _Infinite):
            if m <= 0:
                raise ValueError(
                    f"Expected either ``_Infinite.INFINITE`` or a positive integer for m, got {m}"
                )
        if not isinstance(t, _Quotient):
            if t <= 0:
                raise ValueError(
                    f"Expected either ```_Quotient.QUOTIENT`` or a positive integer for t, got {t}"
                )

    def to_tuple(self) -> tuple[int | _Infinite, int | _Quotient]:
        """Returns the tuple that identifies the Zephyr shape."""
        return (self.m, self.t)

    def to_quotient(self) -> ZephyrShape:
        """Converts the shape to its corresponding quotient tile size shape."""
        return ZephyrShape(m=self.m, t=_Quotient.QUOTIENT)

    def is_quotient(self) -> bool:
        """Tells whether the shape represents a shape with quotient tile size."""
        return self.t is _Quotient.QUOTIENT

    def to_infinite(self) -> TopologyShape:
        """Converts the shape to its corresponding infinite grid size shape."""
        return ZephyrShape(m=_Infinite.INFINITE, t=self.t)

    def is_infinite(self) -> bool:
        """Tells whether the shape represents a shape with infinite grid size."""
        return self.m is _Infinite.INFINITE
