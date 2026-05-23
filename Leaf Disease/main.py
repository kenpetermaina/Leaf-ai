import os
import json
import csv
import time
import requests
from typing import Tuple
import logging
import sys
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

from groq import Groq
from dotenv import load_dotenv


# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class DiseaseAnalysisResult:
    """
    Data class for storing comprehensive disease analysis results.

    This class encapsulates all the information returned from a leaf disease
    analysis, including detection status, disease identification, severity
    assessment, and treatment recommendations.

    Attributes:
        disease_detected (bool): Whether a disease was detected in the leaf image
        disease_name (Optional[str]): Name of the identified disease, None if healthy
        disease_type (str): Category of disease (fungal, bacterial, viral, pest, etc.)
    """
    disease_detected: bool
    disease_name: Optional[str]
    disease_type: str
    severity: str
    confidence: float
    symptoms: List[str]
    possible_causes: List[str]
    treatment: List[str]
    chemical_recommendations: List[str] = field(default_factory=list)
    analysis_timestamp: str = datetime.now().astimezone().isoformat()


CHEMICAL_TREATMENT_MAP = {
    "late blight": ["Mancozeb", "Copper oxychloride", "Chlorothalonil"],
    "powdery mildew": ["Sulfur", "Myclobutanil", "Trifloxystrobin"],
    "bacterial spot": ["Copper hydroxide", "Streptomycin"],
    "anthracnose": ["Mancozeb", "Chlorothalonil"],
    "brown spot": ["Azoxystrobin", "Chlorothalonil"],
    "downy mildew": ["Metalaxyl", "Mefenoxam"],
    "rust": ["Propiconazole", "Tebuconazole"],
    "nutrient deficiency": ["Balanced foliar fertilizer", "Micronutrient spray"],
    "fungal": ["Copper-based fungicide", "Mancozeb", "Chlorothalonil"],
    "bacterial": ["Copper-based bactericide", "Streptomycin"],
    "viral": ["No chemical cure; remove infected plants and control vectors"],
    "pest": ["Pyrethroids", "Spinosad", "Neem oil"]
}

# External chemical recommendations API integration.
# Configure via environment variables: CHEMICALS_API_URL, CHEMICALS_API_KEY (optional)
CHEMICALS_API_URL = os.environ.get('CHEMICALS_API_URL')
CHEMICALS_API_KEY = os.environ.get('CHEMICALS_API_KEY')

# Simple in-memory cache for API results: (timestamp, mapping)
_CHEM_API_CACHE: Tuple[float, Dict[str, List[str]]] = (0.0, {})
_CHEM_API_TTL = int(os.environ.get('CHEMICALS_API_TTL_SECONDS', '3600'))


def _fetch_chemical_map_from_api(url: str, api_key: Optional[str] = None) -> Dict[str, List[str]]:
    mapping: Dict[str, List[str]] = {}
    global _CHEM_API_CACHE
    try:
        now = time.time()
        cached_ts, cached_map = _CHEM_API_CACHE
        if cached_map and (now - cached_ts) < _CHEM_API_TTL:
            return cached_map

        headers = {'Accept': 'application/json'}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # Expected JSON format: { "disease_key": ["chem1", "chem2"], ... }
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(k, str) and isinstance(v, list):
                    mapping[k.strip().lower()] = [str(x).strip() for x in v if str(x).strip()]

        _CHEM_API_CACHE = (now, mapping)
        logger.info(f"Fetched chemical map from API: {url} (entries={len(mapping)})")
    except Exception:
        logger.exception(f"Failed to fetch chemical map from API: {url}")
    return mapping


def get_chemical_recommendations(disease_name: Optional[str], disease_type: str) -> List[str]:
    # Prefer authoritative CSV-based mapping if available
    def _lookup_in_map(mapping: Dict[str, List[str]], name: Optional[str], dtype: str) -> Optional[List[str]]:
        if name:
            k = name.strip().lower()
            if k in mapping:
                return mapping[k]
            for key, chems in mapping.items():
                if key in k:
                    return chems
        dkey = dtype.strip().lower() if dtype else ''
        if dkey in mapping:
            return mapping[dkey]
        for key, chems in mapping.items():
            if key in dkey:
                return chems
        return None

    # Try external API mapping first (if configured)
    if CHEMICALS_API_URL:
        api_map = _fetch_chemical_map_from_api(CHEMICALS_API_URL, CHEMICALS_API_KEY)
        if api_map:
            res = _lookup_in_map(api_map, disease_name, disease_type)
            if res:
                return res

    if disease_name:
        disease_key = disease_name.strip().lower()
        if disease_key in CHEMICAL_TREATMENT_MAP:
            return CHEMICAL_TREATMENT_MAP[disease_key]

        for key, chemicals in CHEMICAL_TREATMENT_MAP.items():
            if key in disease_key:
                return chemicals

    disease_type_key = disease_type.strip().lower() if disease_type else ""
    if disease_type_key in CHEMICAL_TREATMENT_MAP:
        return CHEMICAL_TREATMENT_MAP[disease_type_key]

    for key, chemicals in CHEMICAL_TREATMENT_MAP.items():
        if key in disease_type_key:
            return chemicals

    return []


class LeafDiseaseDetector:
    """
    Advanced Leaf Disease Detection System using AI Vision Analysis.

    This class provides comprehensive leaf disease detection capabilities using
    the Groq API with Llama Vision models. It can analyze leaf images to identify
    diseases, assess severity, and provide treatment recommendations. The system
    also validates that uploaded images contain actual plant leaves and rejects
    images of humans, animals, or other non-plant objects.

    The system supports base64 encoded images and returns structured JSON results
    containing disease information, confidence scores, symptoms, causes, and
    treatment suggestions.

    Features:
        - Image validation (ensures uploaded images contain plant leaves)
        - Multi-disease detection (fungal, bacterial, viral, pest, nutrient deficiency)
        - Severity assessment (mild, moderate, severe)
        - Confidence scoring (0-100%)
        - Symptom identification
        - Treatment recommendations
        - Robust error handling and response parsing
        - Invalid image type detection and rejection

    Attributes:
        MODEL_NAME (str): The AI model used for analysis
        DEFAULT_TEMPERATURE (float): Default temperature for response generation
        DEFAULT_MAX_TOKENS (int): Default maximum tokens for responses
        api_key (str): Groq API key for authentication
        client (Groq): Groq API client instance

    Example:
        >>> detector = LeafDiseaseDetector()
        >>> result = detector.analyze_leaf_image_base64(base64_image_data)
        >>> if result['disease_type'] == 'invalid_image':
        ...     print("Please upload a plant leaf image")
        >>> elif result['disease_detected']:
        ...     print(f"Disease detected: {result['disease_name']}")
        >>> else:
        ...     print("Healthy leaf detected")
    """

    MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"
    DEFAULT_TEMPERATURE = 0.3
    DEFAULT_MAX_TOKENS = 1024

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Leaf Disease Detector with API credentials.

        Sets up the Groq API client and validates the API key from either
        the parameter or environment variables. Initializes logging for
        tracking analysis operations.

        Args:
            api_key (Optional[str]): Groq API key. If None, will attempt to
                                   load from GROQ_API_KEY environment variable.

        Raises:
            ValueError: If no valid API key is found in parameters or environment.

        Note:
            Ensure your .env file contains GROQ_API_KEY or pass it directly.
        """
        load_dotenv()
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        self.client = Groq(api_key=self.api_key)
        logger.info("Leaf Disease Detector initialized")

    def create_analysis_prompt(self) -> str:
        """
        Create the standardized analysis prompt for the AI model.

        Generates a comprehensive prompt that instructs the AI model to analyze
        leaf images for diseases and return structured JSON results. The prompt
        specifies the required output format and analysis criteria.

        Returns:
            str: Formatted prompt string with instructions for disease analysis
                 and JSON schema specification.

        Note:
            The prompt ensures consistent output formatting across all analyses
            and includes all necessary fields for comprehensive disease assessment.
        """
        return """IMPORTANT: First determine if this image contains a plant leaf or vegetation. If the image shows humans, animals, objects, buildings, or anything other than plant leaves/vegetation, return the "invalid_image" response format below.

        If this is a valid leaf/plant image, analyze it for diseases and return the results in JSON format.
        
        Please identify:
        1. Whether this is actually a leaf/plant image
        2. Disease name (if any)
        3. Disease type/category or invalid_image
        4. Severity level (mild, moderate, severe)
        5. Confidence score (0-100%)
        6. Symptoms observed
        7. Possible causes
        8. Treatment recommendations, including commonly used crop protection chemicals, fungicides, bactericides, insecticides, or nutrient support products where applicable.

        For NON-LEAF images (humans, animals, objects, or not detected as leaves, etc.), return this format:
        {
            "disease_detected": false,
            "disease_name": null,
            "disease_type": "invalid_image",
            "severity": "none",
            "confidence": 95,
            "symptoms": ["This image does not contain a plant leaf"],
            "possible_causes": ["Invalid image type uploaded"],
            "treatment": ["Please upload an image of a plant leaf for disease analysis"]
        }
        
        For VALID LEAF images, return this format:
        {
            "disease_detected": true/false,
            "disease_name": "name of disease or null",
            "disease_type": "fungal/bacterial/viral/pest/nutrient deficiency/healthy",
            "severity": "mild/moderate/severe/none",
            "confidence": 85,
            "symptoms": ["list", "of", "symptoms"],
            "possible_causes": ["list", "of", "causes"],
            "treatment": ["list", "of", "treatments"],
            "recommended_chemicals": ["list", "of", "recommended chemicals"]
        }"""

    def analyze_leaf_image_base64(self, base64_image: str,
                                  temperature: float = None,
                                  max_tokens: int = None) -> Dict:
        """
        Analyze base64 encoded image data for leaf diseases and return JSON result.

        First validates that the image contains a plant leaf. If the image shows
        humans, animals, objects, or other non-plant content, returns an 
        'invalid_image' response. For valid leaf images, performs disease analysis.

        Args:
            base64_image (str): Base64 encoded image data (without data:image prefix)
            temperature (float, optional): Model temperature for response generation
            max_tokens (int, optional): Maximum tokens for response

        Returns:
            Dict: Analysis results as dictionary (JSON serializable)
                 - For invalid images: disease_type will be 'invalid_image'
                 - For valid leaves: standard disease analysis results

        Raises:
            Exception: If analysis fails
        """
        try:
            logger.info("Starting analysis for base64 image data")

            # Validate base64 input
            if not isinstance(base64_image, str):
                raise ValueError("base64_image must be a string")

            if not base64_image:
                raise ValueError("base64_image cannot be empty")

            # Clean base64 string (remove data URL prefix if present)
            if base64_image.startswith('data:'):
                base64_image = base64_image.split(',', 1)[1]

            # Prepare request parameters
            temperature = temperature or self.DEFAULT_TEMPERATURE
            max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS

            # Make API request
            completion = self.client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.create_analysis_prompt()
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=temperature,
                max_completion_tokens=max_tokens,
                top_p=1,
                stream=False,
                stop=None,
            )

            logger.info("API request completed successfully")
            result = self._parse_response(
                completion.choices[0].message.content)

            # Return as dictionary for JSON serialization
            return result.__dict__

        except Exception as e:
            logger.error(f"Analysis failed for base64 image data: {str(e)}")
            raise

    def _parse_response(self, response_content: str) -> DiseaseAnalysisResult:
        """
        Parse and validate API response

        Args:
            response_content (str): Raw response from API

        Returns:
            DiseaseAnalysisResult: Parsed and validated results
        """
        try:
            # Clean up response - remove markdown code blocks if present
            cleaned_response = response_content.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace(
                    '```json', '').replace('```', '').strip()
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```', '').strip()

            # Parse JSON
            disease_data = json.loads(cleaned_response)
            logger.info("Response parsed successfully as JSON")

            # Validate required fields and create result object
            return DiseaseAnalysisResult(
                disease_detected=bool(
                    disease_data.get('disease_detected', False)),
                disease_name=disease_data.get('disease_name'),
                disease_type=disease_data.get('disease_type', 'unknown'),
                severity=disease_data.get('severity', 'unknown'),
                confidence=float(disease_data.get('confidence', 0)),
                symptoms=disease_data.get('symptoms', []),
                possible_causes=disease_data.get('possible_causes', []),
                treatment=disease_data.get('treatment', []),
                chemical_recommendations=disease_data.get('recommended_chemicals', []) or get_chemical_recommendations(
                    disease_data.get('disease_name'), disease_data.get('disease_type', 'unknown'))
            )

        except json.JSONDecodeError:
            logger.warning(
                "Failed to parse as JSON, attempting to extract JSON from response")

            # Try to find JSON in the response using regex
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                try:
                    disease_data = json.loads(json_match.group())
                    logger.info("JSON extracted and parsed successfully")

                    return DiseaseAnalysisResult(
                        disease_detected=bool(
                            disease_data.get('disease_detected', False)),
                        disease_name=disease_data.get('disease_name'),
                        disease_type=disease_data.get(
                            'disease_type', 'unknown'),
                        severity=disease_data.get('severity', 'unknown'),
                        confidence=float(disease_data.get('confidence', 0)),
                        symptoms=disease_data.get('symptoms', []),
                        possible_causes=disease_data.get(
                            'possible_causes', []),
                        treatment=disease_data.get('treatment', []),
                        chemical_recommendations=disease_data.get('recommended_chemicals', []) or get_chemical_recommendations(
                            disease_data.get('disease_name'), disease_data.get('disease_type', 'unknown'))
                    )
                except json.JSONDecodeError:
                    pass

            # If all parsing attempts fail, log the raw response and raise error
            logger.error(
                f"Could not parse response as JSON. Raw response: {response_content}")
            raise ValueError(
                f"Unable to parse API response as JSON: {response_content[:200]}...")


def main():
    """Main execution function for testing"""
    try:
        # Example usage
        detector = LeafDiseaseDetector()
        print("Leaf Disease Detector (minimal version) initialized successfully!")
        print("Use analyze_leaf_image_base64() method with base64 image data.")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
