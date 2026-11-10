"""Actual rectangular mesh, x-periodic MPC and pressure gauge preparation.

No variational form is assembled and no PDE is solved by this package.
"""

from .interface import (attach_checked_pressure_nullspace, build_interface,
                        remove_pressure_area_mean)

__all__ = ["attach_checked_pressure_nullspace", "build_interface",
           "remove_pressure_area_mean"]
