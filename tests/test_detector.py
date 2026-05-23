import json
import os
import importlib.util
from pathlib import Path


def load_leaf_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "Leaf Disease" / "main.py"
    # Inject a dummy 'groq' module to avoid external dependency during import
    import sys, types
    if 'groq' not in sys.modules:
        groq_mod = types.ModuleType('groq')
        class Groq:
            def __init__(self, *args, **kwargs):
                pass
        groq_mod.Groq = Groq
        sys.modules['groq'] = groq_mod

    spec = importlib.util.spec_from_file_location("leaf_module", str(module_path))
    leaf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(leaf)
    return leaf


def test_get_chemical_recommendations_by_name():
    leaf = load_leaf_module()
    res = leaf.get_chemical_recommendations("Late blight", "fungal")
    assert isinstance(res, list)
    assert any("mancozeb" in c.lower() for c in res)


def test_get_chemical_recommendations_by_type():
    leaf = load_leaf_module()
    res = leaf.get_chemical_recommendations(None, "fungal")
    assert isinstance(res, list)
    assert len(res) > 0


def test_parse_response_json():
    leaf = load_leaf_module()
    detector = leaf.LeafDiseaseDetector.__new__(leaf.LeafDiseaseDetector)
    sample = json.dumps({
        "disease_detected": True,
        "disease_name": "Late Blight",
        "disease_type": "fungal",
        "severity": "severe",
        "confidence": 92,
        "symptoms": ["dark lesions"],
        "possible_causes": ["high humidity"],
        "treatment": ["apply fungicide"]
    })
    result = detector._parse_response(sample)
    assert result.disease_detected is True
    assert result.disease_name.lower() == "late blight"
    assert "fungal" in result.disease_type


def test_parse_response_codeblock():
    leaf = load_leaf_module()
    detector = leaf.LeafDiseaseDetector.__new__(leaf.LeafDiseaseDetector)
    sample = "```json\n" + json.dumps({
        "disease_detected": False,
        "disease_name": None,
        "disease_type": "invalid_image",
        "severity": "none",
        "confidence": 95,
        "symptoms": ["This image does not contain a plant leaf"],
        "possible_causes": ["Invalid image type uploaded"],
        "treatment": ["Please upload an image of a plant leaf for disease analysis"]
    }) + "\n```"
    result = detector._parse_response(sample)
    assert result.disease_type == "invalid_image"


if __name__ == "__main__":
    # Simple runner for environments without pytest available
    tests = [
        test_get_chemical_recommendations_by_name,
        test_get_chemical_recommendations_by_type,
        test_parse_response_json,
        test_parse_response_codeblock,
    ]
    for t in tests:
        print(f"Running {t.__name__}...")
        t()
    print("All tests passed")
