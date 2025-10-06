"""
Data extractors module with strategy pattern
"""

from .natural_extractor import NaturalExtractor
from .chain_of_thought_extractor import ChainOfThoughtExtractor
from .page_by_page_extractor import PageByPageExtractor
from .extractor_factory import ExtractorFactory
from .extraction_strategies import ExtractionStrategy, AutoExtractionStrategy

__all__ = [
    'NaturalExtractor',
    'ChainOfThoughtExtractor',
    'PageByPageExtractor',
    'ExtractorFactory',
    'ExtractionStrategy',
    'AutoExtractionStrategy'
]
