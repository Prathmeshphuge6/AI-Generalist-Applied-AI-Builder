import pytest
from pydantic import ValidationError
import json

import analyzer
from models import DDRReport

# ==========================================
# Mock Outputs for Each Stage
# ==========================================
MOCK_STAGE_1 = [
    {
        "area": "Bathroom",
        "defect": "Dampness",
        "description": "Visible dampness on ceiling",
        "source_document": "Inspection Report",
        "page_number": 2,
        "image_id": "IMG_001"
    }
]

MOCK_STAGE_2 = {
    "Bathroom": [
        {
            "defect": "Dampness",
            "description": "Visible dampness on ceiling",
            "source_document": "Inspection Report",
            "page_number": 2,
            "image_id": "IMG_001"
        }
    ]
}

MOCK_STAGE_3 = [
    {
        "id": "OBS-001",
        "area": "Bathroom",
        "defect": "Dampness",
        "description": "Ceiling dampness confirmed by visual inspection.",
        "evidence": [
            {
                "source_document": "Inspection Report",
                "page_number": 2,
                "image_id": "IMG_001"
            }
        ]
    }
]

MOCK_STAGE_4 = [
    {
        "id": "OBS-001",
        "area": "Bathroom",
        "defect": "Dampness",
        "description": "Ceiling dampness confirmed by visual inspection.",
        "evidence": [
            {
                "source_document": "Inspection Report",
                "page_number": 2,
                "image_id": "IMG_001"
            }
        ],
        "is_conflict": False,
        "conflict_details": None
    }
]

MOCK_STAGE_5 = [
    {
        "id": "OBS-001",
        "area": "Bathroom",
        "defect": "Dampness",
        "description": "Ceiling dampness confirmed by visual inspection.",
        "evidence": [
            {
                "source_document": "Inspection Report",
                "page_number": 2,
                "image_id": "IMG_001"
            }
        ],
        "is_conflict": False,
        "conflict_details": None,
        "probable_root_cause": "Waterproofing failure"
    }
]

MOCK_STAGE_6 = [
    {
        "id": "OBS-001",
        "area": "Bathroom",
        "defect": "Dampness",
        "description": "Ceiling dampness confirmed by visual inspection.",
        "evidence": [
            {
                "source_document": "Inspection Report",
                "page_number": 2,
                "image_id": "IMG_001"
            }
        ],
        "is_conflict": False,
        "conflict_details": None,
        "probable_root_cause": "Waterproofing failure",
        "severity": "Medium",
        "reasoning": "Localized moisture issue, not structurally threatening.",
        "confidence": "High",
        "repair_procedure": ["1. Remove existing grout.", "2. Re-apply waterproofing coat."],
        "estimated_cost": "₹15,000 - ₹20,000",
        "materials_required": ["Waterproof Grout", "Polymer coating"],
        "priority": "Medium",
        "timeline": "Within 30 Days",
        "confidence_breakdown": {
            "Inspection Evidence": 97,
            "Thermal Evidence": 94,
            "Image Evidence": 91,
            "Overall": 95
        }
    }
]

MOCK_STAGE_7 = [
    {
        "priority": "Short-term Actions",
        "action_type": "Waterproofing",
        "description": "Reseal bathroom floor waterproofing.",
        "associated_observation_ids": ["OBS-001"]
    }
]

MOCK_STAGE_8 = {
    "executive_summary": "Property is in generally good condition with localized bathroom moisture issues.",
    "overall_severity": "Medium",
    "reasoning": "No structural instability detected. Medium repairs required in bathroom.",
    "risk_score": 35,
    "priority_ranking": ["Bathroom"],
    "structural_health": 91,
    "waterproofing_health": 52,
    "interior_finish_health": 63,
    "moisture_risk": "High"
}

# The final Stage 9 returns the full unified report matching the Pydantic schema
MOCK_STAGE_9 = {
    "property_info": {
        "address": "123 Tech Blvd",
        "client_name": "ACME",
        "inspection_date": "2026-07-07"
    },
    "executive_summary": "Property is in generally good condition with localized bathroom moisture issues.",
    "observations": MOCK_STAGE_6,
    "severity_assessment": MOCK_STAGE_8,
    "recommendations": MOCK_STAGE_7,
    "missing_information": [
        {
            "item_category": "Thermal readings",
            "description": "Thermal readings were not provided for checking insulation levels."
        }
    ],
    "final_engineering_assessment": "This is a final engineering assessment conclusion.",
    "estimated_total_cost_range": "₹48,000 - ₹62,000"
}

# ==========================================
# Mock Call Selector
# ==========================================
def get_mock_response(prompt_text: str) -> str:
    """
    Simulates Gemini API responses for the consolidated stages
    by inspecting string constants inside prompts.
    """
    if "STAGE_7_SYNTHESIS" in prompt_text or "PROPERTY INFO" in prompt_text:
        return json.dumps(MOCK_STAGE_9)
    elif "STAGE_1_EXTRACT_OBS" in prompt_text or "VISUAL INSPECTION REPORT" in prompt_text:
        return json.dumps({"observations": MOCK_STAGE_1})
    elif "STAGE_3_ANALYSIS" in prompt_text or "grouped_observations" in prompt_text:
        return json.dumps({"observations": MOCK_STAGE_6})
    
    # Fallback default
    return json.dumps(MOCK_STAGE_9)

def test_run_analysis_pipeline(monkeypatch):
    """
    Tests the 9-stage analysis pipeline using monkeypatched local responses.
    Verifies that the mock inputs are parsed and compiled into a valid Pydantic DDRReport.
    """
    # Mock the call_llm function to return our staged mock outputs
    def mock_call_llm(prompt_text, system_instruction=None, json_mode=True, schema=None, max_tokens=None):
        return get_mock_response(prompt_text)
        
    monkeypatch.setattr(analyzer, "call_llm", mock_call_llm)
    
    # Track execution stages using callback
    stages_hit = []
    def progress_callback(stage, message):
        stages_hit.append(stage)
        
    # Execute pipeline
    report = analyzer.run_analysis_pipeline(
        visual_text="Mock Visual",
        thermal_text="Mock Thermal",
        images_metadata=[],
        address="123 Tech Blvd",
        client_name="ACME",
        inspection_date="2026-07-07",
        progress_callback=progress_callback
    )
    
    # Assertions
    assert isinstance(report, DDRReport)
    assert len(stages_hit) == 9
    assert stages_hit == [1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert report.property_info.address == "123 Tech Blvd"
    assert report.property_info.client_name == "ACME"
    assert len(report.observations) == 1
    assert report.observations[0].area == "Bathroom"
    assert report.observations[0].defect == "Dampness"
    assert report.severity_assessment.risk_score == 35
    assert len(report.recommendations) == 1
    assert len(report.missing_information) == 1


# ==========================================
# Tests for Truncated JSON Repair
# ==========================================
def test_repair_truncated_json_basic():
    """Tests repair of a JSON array of objects truncated mid-string."""
    truncated = '''{
  "observations": [
    {
      "area": "Hall",
      "defect": "Dampness",
      "description": "Skirting level dampness.",
      "source_document": "Inspection Report",
      "page_number": 3,
      "image_id": "IMG_001"
    },
    {
      "area": "Bathroom",
      "defect": "Tile gaps",
      "description": "Observed gaps between'''
    
    result = analyzer.repair_truncated_json(truncated)
    assert result is not None
    assert "observations" in result
    assert len(result["observations"]) == 1  # Only the first complete object
    assert result["observations"][0]["area"] == "Hall"


def test_repair_truncated_json_multiple_complete():
    """Tests repair preserves multiple complete objects before the truncation."""
    truncated = '''{
  "observations": [
    {
      "area": "Hall",
      "defect": "Dampness",
      "description": "Dampness at skirting.",
      "source_document": "Inspection Report",
      "page_number": 3,
      "image_id": "IMG_001"
    },
    {
      "area": "Kitchen",
      "defect": "Crack",
      "description": "Wall crack observed.",
      "source_document": "Inspection Report",
      "page_number": 4,
      "image_id": "IMG_002"
    },
    {
      "area": "Bedroom",
      "defect": "Dampness",
      "description": "Observed dampness at'''
    
    result = analyzer.repair_truncated_json(truncated)
    assert result is not None
    assert len(result["observations"]) == 2  # Hall + Kitchen, not the truncated Bedroom
    assert result["observations"][0]["area"] == "Hall"
    assert result["observations"][1]["area"] == "Kitchen"


def test_safe_parse_json_with_truncated_input():
    """Tests that safe_parse_json falls through to repair for truncated JSON."""
    truncated = '''{
  "observations": [
    {
      "area": "Roof",
      "defect": "Leakage",
      "description": "Water leakage on roof.",
      "source_document": "Thermal Report",
      "page_number": 1,
      "image_id": "IMG_010"
    },
    {
      "area": "Parking",
      "defect": "Seepage",
      "description": "Seepage observed at'''
    
    result = analyzer.safe_parse_json(truncated)
    assert result is not None
    assert len(result["observations"]) == 1
    assert result["observations"][0]["area"] == "Roof"
