"""
Extraction strategies using strategy pattern
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import json

try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    print("⚠️  DSPy not available. Some features may be limited.")

from core.base_classes import BaseDataExtractor
from core.interfaces import IExtractionStrategy
from core.exceptions import ExtractionError


class ExtractionStrategy(IExtractionStrategy):
    """Base extraction strategy"""
    
    def __init__(self, api_key: str, model_name: str = "openai/gpt-4o-mini", use_azure: bool = False):
        self.api_key = api_key
        self.model_name = model_name
        self.use_azure = use_azure
        self.strategy_name = "base"
    
    @abstractmethod
    def extract(self, document_text: str, document_image: Any, document_type: str) -> Dict[str, Any]:
        """Extract data using this strategy"""
        pass
    
    def get_strategy_name(self) -> str:
        """Get the name of this extraction strategy"""
        return self.strategy_name
    
    def _parse_json_result(self, raw_result: str) -> Dict[str, Any]:
        """Parse JSON result with error handling"""
        try:
            return json.loads(raw_result)
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parsing failed: {e}")
            print(f"Raw output: {raw_result[:200]}...")
            
            # Try to fix common JSON issues
            fixed_json = self._fix_incomplete_json(raw_result)
            if fixed_json:
                try:
                    return json.loads(fixed_json)
                except json.JSONDecodeError:
                    return {"raw_extraction": raw_result}
            else:
                return {"raw_extraction": raw_result}
    
    def _fix_incomplete_json(self, json_str: str) -> str:
        """Try to fix common JSON issues like incomplete JSON"""
        try:
            import re
            
            # Fix trailing commas before closing braces
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            # If JSON is incomplete (missing closing braces), try to complete it
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            open_brackets = json_str.count('[')
            close_brackets = json_str.count(']')
            
            # Add missing closing braces
            missing_braces = open_braces - close_braces
            missing_brackets = open_brackets - close_brackets
            
            if missing_braces > 0 or missing_brackets > 0:
                # Add missing closing brackets first
                for _ in range(missing_brackets):
                    json_str += ']'
                
                # Add missing closing braces
                for _ in range(missing_braces):
                    json_str += '}'
                
                print(f"🔧 Attempted to fix incomplete JSON by adding {missing_braces} braces and {missing_brackets} brackets")
            
            return json_str
            
        except Exception as e:
            print(f"⚠️  Error fixing JSON: {e}")
            return None


class NaturalExtractionStrategy(ExtractionStrategy):
    """Natural extraction strategy using DSPy without structured prompting"""
    
    def __init__(self, api_key: str, model_name: str = "openai/gpt-4o-mini", use_azure: bool = False):
        super().__init__(api_key, model_name, use_azure)
        self.strategy_name = "natural"
        self._setup_dspy()
    
    def _setup_dspy(self):
        """Setup DSPy for natural extraction"""
        from llm_config import LLMConfig
        
        llm_config = LLMConfig(use_azure=self.use_azure)
        self.lm = llm_config.get_lm()
        
        # Define natural extraction signature
        class NaturalExtractionSignature(dspy.Signature):
            """Extract structured data from document and return as JSON format. Example: {\"patient_name\": \"John Doe\", \"age\": 30, \"lab_results\": {\"glucose\": \"95 mg/dL\"}}"""
            document_text: str = dspy.InputField()
            document_image: dspy.Image = dspy.InputField()
            
            extracted_data: str = dspy.OutputField(desc="Extract all relevant data and return as valid JSON object only, no markdown formatting")
        
        self.extractor = dspy.Predict(NaturalExtractionSignature)
    
    def extract(self, document_text: str, document_image: Any, document_type: str) -> Dict[str, Any]:
        """Extract data using natural DSPy extraction"""
        try:
            # Convert PIL image to dspy.Image if needed
            if hasattr(document_image, 'image_object'):
                image_obj = dspy.Image.from_PIL(document_image['image_object'])
            else:
                image_obj = document_image
            
            # Extract data using DSPy
            result = self.extractor(
                document_text=document_text,
                document_image=image_obj
            )
            
            # Parse and return result
            parsed_data = self._parse_json_result(result.extracted_data)
            
            return {
                'success': True,
                'data': parsed_data,
                'strategy': self.strategy_name,
                'confidence': 1.0
            }
            
        except Exception as e:
            raise ExtractionError(f"Natural extraction failed: {str(e)}")


class ChainOfThoughtExtractionStrategy(ExtractionStrategy):
    """Chain-of-thought extraction strategy for complex reasoning"""
    
    def __init__(self, api_key: str, model_name: str = "openai/gpt-4o-mini", use_azure: bool = False):
        super().__init__(api_key, model_name, use_azure)
        self.strategy_name = "chain_of_thought"
        self._setup_dspy()
    
    def _setup_dspy(self):
        """Setup DSPy for chain-of-thought extraction"""
        from llm_config import LLMConfig
        
        llm_config = LLMConfig(use_azure=self.use_azure)
        self.lm = llm_config.get_lm()
        
        # Define chain-of-thought extraction signature
        class ChainOfThoughtExtractionSignature(dspy.Signature):
            """Extract structured data from document using step-by-step reasoning and return as JSON format. Example: {\"patient_name\": \"John Doe\", \"age\": 30, \"lab_results\": {\"glucose\": \"95 mg/dL\"}}"""
            document_text: str = dspy.InputField()
            document_image: dspy.Image = dspy.InputField()
            
            reasoning: str = dspy.OutputField(desc="Step-by-step reasoning for data extraction")
            extracted_data: str = dspy.OutputField(desc="Extract all relevant data and return as valid JSON object only, no markdown formatting")
        
        self.extractor = dspy.ChainOfThought(ChainOfThoughtExtractionSignature)
    
    def extract(self, document_text: str, document_image: Any, document_type: str) -> Dict[str, Any]:
        """Extract data using chain-of-thought reasoning"""
        try:
            # Convert PIL image to dspy.Image if needed
            if hasattr(document_image, 'image_object'):
                image_obj = dspy.Image.from_PIL(document_image['image_object'])
            else:
                image_obj = document_image
            
            # Extract data using DSPy chain-of-thought
            result = self.extractor(
                document_text=document_text,
                document_image=image_obj
            )
            
            # Parse and return result
            parsed_data = self._parse_json_result(result.extracted_data)
            
            return {
                'success': True,
                'data': parsed_data,
                'reasoning': result.reasoning,
                'strategy': self.strategy_name,
                'confidence': 1.0
            }
            
        except Exception as e:
            raise ExtractionError(f"Chain-of-thought extraction failed: {str(e)}")


class AutoExtractionStrategy(ExtractionStrategy):
    """Auto extraction strategy that selects the best method based on document characteristics"""
    
    def __init__(self, api_key: str, model_name: str = "openai/gpt-4o-mini", use_azure: bool = False):
        super().__init__(api_key, model_name, use_azure)
        self.strategy_name = "auto"
        
        # Initialize sub-strategies
        self.natural_strategy = NaturalExtractionStrategy(api_key, model_name, use_azure)
        self.chain_of_thought_strategy = ChainOfThoughtExtractionStrategy(api_key, model_name, use_azure)
    
    def extract(self, document_text: str, document_image: Any, document_type: str) -> Dict[str, Any]:
        """Automatically select and use the best extraction strategy"""
        try:
            # Analyze document characteristics
            text_length = len(document_text)
            has_images = document_image is not None
            
            # Select strategy based on characteristics
            if text_length > 1000:
                # Use chain-of-thought for complex documents
                strategy = self.chain_of_thought_strategy
                print("📊 Using chain-of-thought strategy for complex document")
            else:
                # Use natural extraction for simpler documents
                strategy = self.natural_strategy
                print("📊 Using natural strategy for simple document")
            
            # Extract data using selected strategy
            result = strategy.extract(document_text, document_image, document_type)
            result['strategy'] = self.strategy_name
            result['selected_sub_strategy'] = strategy.get_strategy_name()
            
            return result
            
        except Exception as e:
            raise ExtractionError(f"Auto extraction failed: {str(e)}")
