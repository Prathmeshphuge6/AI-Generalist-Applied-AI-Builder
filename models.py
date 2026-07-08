from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class PropertyInfo(BaseModel):
    """
    Pydantic model containing metadata about the property and inspection.
    """
    address: str = Field(
        ..., 
        description="Full address or description of the property. Must be 'Not Available' if missing."
    )
    client_name: str = Field(
        default="Not Available", 
        description="Name of the client/owner. Must be 'Not Available' if missing."
    )
    inspection_date: str = Field(
        default="Not Available", 
        description="Date of the inspection. Must be 'Not Available' if missing."
    )


class EvidenceSource(BaseModel):
    """
    Model linking an observation back to specific source documents and evidence.
    """
    source_document: str = Field(
        ..., 
        description="The source report, e.g., 'Inspection Report' or 'Thermal Report'."
    )
    page_number: int = Field(
        ..., 
        description="The page number where the observation was found (1-indexed)."
    )
    image_id: Optional[str] = Field(
        default=None, 
        description="The unique identifier of the extracted image supporting this observation (e.g. 'IMG_001.png'), if any."
    )


class Observation(BaseModel):
    """
    Model representing a distinct building diagnostic observation.
    """
    id: str = Field(
        ..., 
        description="Unique identifier for the observation, e.g., 'OBS-001', 'OBS-002'."
    )
    area: str = Field(
        ..., 
        description="The affected area in the property, e.g., 'Roof', 'Bathroom', 'Kitchen'."
    )
    defect: str = Field(
        ..., 
        description="The type of defect detected, e.g., 'Dampness', 'Crack', 'Water Ingress', 'Efflorescence'."
    )
    description: str = Field(
        ..., 
        description="A detailed description of the physical findings, thermal findings, and correlation."
    )
    evidence: List[EvidenceSource] = Field(
        ..., 
        description="List of specific report occurrences and images that back this finding."
    )
    severity: str = Field(
        ..., 
        description="Severity classification. Must be one of: 'Low', 'Medium', 'High', 'Critical'."
    )
    reasoning: str = Field(
        ..., 
        description="Detailed explanation of WHY the specific severity level was assigned based on evidence."
    )
    confidence: str = Field(
        ..., 
        description="Calculated confidence level. Must be one of: 'Low', 'Medium', 'High', 'Very High'."
    )
    probable_root_cause: str = Field(
        default="Not Available", 
        description="The inferred probable root cause, e.g., 'Roof waterproofing failure', 'Pipe leakage'. Use 'Not Available' if evidence is insufficient."
    )
    is_conflict: bool = Field(
        default=False,
        description="Flags whether conflicting observations were detected between visual and thermal reports for this finding."
    )
    conflict_details: Optional[str] = Field(
        default=None,
        description="Details of the conflict and the engineering recommendation to resolve it."
    )
    repair_procedure: List[str] = Field(
        ...,
        description="Detailed step-by-step sequential engineering repair procedure."
    )
    estimated_cost: str = Field(
        ...,
        description="Estimated cost range, e.g., '₹15,000 - ₹20,000'."
    )
    materials_required: List[str] = Field(
        ...,
        description="List of materials required for the repair."
    )
    priority: str = Field(
        ...,
        description="Priority level. Must be one of: 'Critical', 'High', 'Medium', 'Low'."
    )
    timeline: str = Field(
        ...,
        description="Urgency timeline. Must be one of: 'Within 24 Hours', 'Within 7 Days', 'Within 30 Days', 'Routine Maintenance'."
    )
    confidence_breakdown: Dict[str, int] = Field(
        ...,
        description="Calculated confidence breakdown, e.g. {'Inspection Evidence': 97, 'Thermal Evidence': 94, 'Image Evidence': 91, 'Overall': 95}."
    )


class SeverityAssessment(BaseModel):
    """
    Overall risk assessment for the entire property.
    """
    overall_severity: str = Field(
        ..., 
        description="Overall severity rating. Must be one of: 'Low', 'Medium', 'High', 'Critical'."
    )
    reasoning: str = Field(
        ..., 
        description="Explanation of the overall risk profile and structural/safety implications."
    )
    risk_score: int = Field(
        ..., 
        description="A calculated numerical risk score for the property from 0 (Perfect Condition) to 100 (Immediate Hazard).",
        ge=0,
        le=100
    )
    priority_ranking: List[str] = Field(
        ..., 
        description="List of areas ranked by repair priority (highest risk to lowest)."
    )
    structural_health: int = Field(
        ...,
        description="Structural Health percentage, 0-100."
    )
    waterproofing_health: int = Field(
        ...,
        description="Waterproofing Health percentage, 0-100."
    )
    interior_finish_health: int = Field(
        ...,
        description="Interior Finish Health percentage, 0-100."
    )
    moisture_risk: str = Field(
        ...,
        description="Overall moisture risk level. Must be one of: 'Low', 'Medium', 'High', 'Critical'."
    )


class Recommendation(BaseModel):
    """
    Model representing an actionable remedy or maintenance step.
    """
    priority: str = Field(
        ..., 
        description="Urgency tier. Must be one of: 'Immediate Actions', 'Short-term Actions', 'Long-term Preventive Actions'."
    )
    action_type: str = Field(
        ..., 
        description="The type of repair action, e.g., 'Waterproofing', 'Structural Repair', 'Monitoring', 'Plumbing'."
    )
    description: str = Field(
        ..., 
        description="Detailed step-by-step description of the recommended action."
    )
    associated_observation_ids: List[str] = Field(
        ..., 
        description="List of unique observation IDs (e.g., ['OBS-001']) this recommendation addresses."
    )


class MissingInformation(BaseModel):
    """
    Model documenting missing information that affects diagnostic certainty.
    """
    item_category: str = Field(
        ..., 
        description="The name/category of the missing information, e.g., 'Moisture readings', 'Property age'."
    )
    description: str = Field(
        ..., 
        description="Description of what is missing, why it is critical, and recommendations to acquire it."
    )


class DDRReport(BaseModel):
    """
    The final schema representing the complete Detailed Diagnostic Report (DDR).
    """
    property_info: PropertyInfo = Field(
        ..., 
        description="Basic property and metadata details."
    )
    executive_summary: str = Field(
        ..., 
        description="A professional, 20+ year veteran tone executive summary of the overall property health."
    )
    observations: List[Observation] = Field(
        ..., 
        description="Consolidated, merged, and cross-referenced observations of property issues."
    )
    severity_assessment: SeverityAssessment = Field(
        ..., 
        description="Overall risk score, priority ranking, and assessment reasoning."
    )
    recommendations: List[Recommendation] = Field(
        ..., 
        description="Actionable repairs categorized by timeframe."
    )
    missing_information: List[MissingInformation] = Field(
        ..., 
        description="Information that was not available in the provided documentation."
    )
    final_engineering_assessment: str = Field(
        ...,
        description="Detailed conclusion summarizing findings, risks, and recommended program."
    )
    estimated_total_cost_range: str = Field(
        ...,
        description="Estimated overall cost range for all observations, e.g., '₹48,000 - ₹62,000'."
    )


# ==========================================
# Pydantic Schemas for Multi-Stage AI Pipeline
# ==========================================

class Stage1Observation(BaseModel):
    area: str = Field(..., description="Affected property area, e.g., Bathroom, Roof")
    defect: str = Field(..., description="Type of defect, e.g., Dampness, Crack")
    description: str = Field(..., description="Text description of visual or thermal finding")
    source_document: str = Field(..., description="E.g., 'Inspection Report' or 'Thermal Report'")
    page_number: int = Field(..., description="Page number where the observation was found")
    image_id: Optional[str] = Field(default=None, description="Comma-separated image IDs or null")

class Stage1Response(BaseModel):
    observations: List[Stage1Observation]

class Stage2Response(BaseModel):
    grouped_observations: Dict[str, List[Stage1Observation]]

class Stage3Observation(BaseModel):
    id: str = Field(..., description="Unique observation ID, e.g., OBS-001")
    area: str = Field(..., description="Property area")
    defect: str = Field(..., description="Merged defect type")
    description: str = Field(..., description="Consolidated description matching visual and thermal details")
    evidence: List[EvidenceSource] = Field(..., description="Linked evidence pages and image IDs")

class Stage3Response(BaseModel):
    consolidated_observations: List[Stage3Observation]

class Stage4Observation(BaseModel):
    id: str
    area: str
    defect: str
    description: str
    evidence: List[EvidenceSource]
    is_conflict: bool = Field(..., description="True if visual and thermal scans contradict")
    conflict_details: Optional[str] = Field(default=None, description="Details of the conflict and recommendation to resolve")

class Stage4Response(BaseModel):
    observations: List[Stage4Observation]

class Stage5Observation(BaseModel):
    id: str
    area: str
    defect: str
    description: str
    evidence: List[EvidenceSource]
    is_conflict: bool
    conflict_details: Optional[str] = None
    probable_root_cause: str = Field(..., description="Inferred probable root cause")

class Stage5Response(BaseModel):
    observations: List[Stage5Observation]

class Stage6Observation(BaseModel):
    id: str
    area: str
    defect: str
    description: str
    evidence: List[EvidenceSource]
    is_conflict: bool
    conflict_details: Optional[str] = None
    probable_root_cause: str
    severity: str = Field(..., description="Low, Medium, High, or Critical")
    reasoning: str = Field(..., description="Explanation of assigned severity")
    confidence: str = Field(..., description="Low, Medium, High, or Very High")
    repair_procedure: List[str]
    estimated_cost: str
    materials_required: List[str]
    priority: str
    timeline: str
    confidence_breakdown: Dict[str, int]

class Stage6Response(BaseModel):
    observations: List[Stage6Observation]

class Stage7Response(BaseModel):
    recommendations: List[Recommendation]

class Stage8Response(BaseModel):
    executive_summary: str = Field(..., description="High-level engineering summary")
    overall_severity: str = Field(..., description="Low, Medium, High, or Critical")
    reasoning: str = Field(..., description="Explanation of the overall risk")
    risk_score: int = Field(..., ge=0, le=100)
    priority_ranking: List[str] = Field(..., description="Ranked list of areas")
