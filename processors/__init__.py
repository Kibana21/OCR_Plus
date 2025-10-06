"""
Document processors module with proper OOP structure
"""

# Import only the factory for now to avoid heavy dependencies
from .processor_factory import ProcessorFactory

__all__ = [
    'ProcessorFactory'
]
