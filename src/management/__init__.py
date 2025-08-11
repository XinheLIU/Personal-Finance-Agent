"""
Management Module
Oversees the entire system, coordinating all other modules.
Starts and stops strategies, adjusts weights, manages risk and capital allocation.
"""

from .coordinator import SystemCoordinator

__all__ = ['SystemCoordinator']