import pytest
from pathlib import Path
import os

from report_generator import generate_docx_report, generate_pdf_report
from models import DDRReport, PropertyInfo, Observation, EvidenceSource, SeverityAssessment, Recommendation, MissingInformation
from config import REPORT_DIR

@pytest.fixture
def sample_ddr_report() -> DDRReport:
    """
    Returns a sample populated DDRReport model object to run tests against.
    """
    prop = PropertyInfo(
        address="100 Test Lane",
        client_name="Test Client",
        inspection_date="2026-07-07"
    )
    
    evidence = [
        EvidenceSource(
            source_document="Inspection Report",
            page_number=3,
            image_id=None
        )
    ]
    
    observations = [
        Observation(
            id="OBS-001",
            area="Roof",
            defect="Membrane deterioration",
            description="Visual checking shows structural cracks in roof coating.",
            evidence=evidence,
            severity="High",
            reasoning="Major risk of water ingress if left untreated.",
            confidence="Medium",
            probable_root_cause="Roof waterproofing failure",
            is_conflict=False,
            conflict_details=None,
            repair_procedure=["1. Step A", "2. Step B"],
            estimated_cost="₹15,000 - ₹20,000",
            materials_required=["Polymer Mortar"],
            priority="High",
            timeline="Within 7 Days",
            confidence_breakdown={"Inspection Evidence": 97, "Thermal Evidence": 94, "Image Evidence": 91, "Overall": 95}
        )
    ]
    
    severity_assessment = SeverityAssessment(
        overall_severity="High",
        reasoning="Critical risk localized on roof membrane cracking.",
        risk_score=70,
        priority_ranking=["Roof"],
        structural_health=91,
        waterproofing_health=52,
        interior_finish_health=63,
        moisture_risk="High"
    )
    
    recommendations = [
        Recommendation(
            priority="Short-term Actions",
            action_type="Waterproofing",
            description="Re-seal and cover membrane cracks on the main roof.",
            associated_observation_ids=["OBS-001"]
        )
    ]
    
    missing_info = [
        MissingInformation(
            item_category="Moisture readings",
            description="Dampness metrics were omitted from visual pages."
        )
    ]
    
    return DDRReport(
        property_info=prop,
        executive_summary="The property was analyzed and exhibits localized high severity issues on the roof.",
        observations=observations,
        severity_assessment=severity_assessment,
        recommendations=recommendations,
        missing_information=missing_info,
        final_engineering_assessment="This is a final engineering assessment.",
        estimated_total_cost_range="₹48,000 - ₹62,000"
    )

def test_generate_docx_report(sample_ddr_report):
    """
    Verifies that generate_docx_report successfully writes a DOCX document to the target directory.
    """
    filename = "test_run_output.docx"
    target_path = REPORT_DIR / filename
    
    # Clean file if it exists from a previous crash
    if target_path.exists():
        target_path.unlink()
        
    try:
        saved_path = generate_docx_report(sample_ddr_report, [], filename=filename)
        
        assert saved_path == target_path
        assert saved_path.exists()
        assert saved_path.stat().st_size > 0
    finally:
        # Cleanup
        if target_path.exists():
            target_path.unlink()

def test_generate_pdf_report(sample_ddr_report):
    """
    Verifies that generate_pdf_report successfully compiles a PDF document via ReportLab.
    """
    filename = "test_run_output.pdf"
    target_path = REPORT_DIR / filename
    
    # Clean file if it exists
    if target_path.exists():
        target_path.unlink()
        
    try:
        saved_path = generate_pdf_report(sample_ddr_report, [], filename=filename)
        
        assert saved_path == target_path
        assert saved_path.exists()
        assert saved_path.stat().st_size > 0
    finally:
        # Cleanup
        if target_path.exists():
            target_path.unlink()
