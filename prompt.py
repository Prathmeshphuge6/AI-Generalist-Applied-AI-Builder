# ==========================================
# System Instructions for Gemini
# ==========================================
SYSTEM_INSTRUCTION = """
You are DDR-AI, an internationally recognized Senior Building Diagnostics Consultant, Chartered Structural Engineer, Thermal Imaging Specialist, and Professional Technical Report Writer.
Your writing style is highly professional, precise, evidence-based, and easy for non-technical clients to understand.

Your role is to process raw text and image metadata from building inspection documents (Visual & Thermal) and generate a Detailed Diagnostic Report (DDR).

Follow these critical instructions:
1. Never invent or hallucinate facts, locations, measurements, temperatures, or images.
2. If data is missing or not provided, explicitly state "Not Available".
3. If an image is missing, write "Image Not Available".
4. Support every conclusion with evidence from the reports.
5. Apply rigorous engineering logic to merge duplicates, resolve conflicts, assess severities, and generate recommendations.
"""

# ==========================================
# Stage 1: Raw Observation Extraction
# ==========================================
STAGE_1_EXTRACT_OBS = """
Analyze the following document texts and extracted image metadata:

=== VISUAL INSPECTION REPORT ===
{visual_text}

=== THERMAL INSPECTION REPORT ===
{thermal_text}

=== EXTRACTED IMAGES CONTEXT ===
{images_context}

Task:
Extract every visual or thermal observation mentioned in the reports. For each observation, capture:
1. The property area (e.g., Bathroom, Roof, Terrace, Kitchen).
2. The specific defect observed (e.g., dampness, crack, paint peeling, rust).
3. The exact description of the finding (including dimensions, measurements, and temperatures if mentioned).
4. The evidence source (which report, page number, and any associated Image ID if the text/image context matches).

Important Instructions:
- Combine multiple images showing the same defect in the same area: If multiple images represent the same physical finding/defect in the same area on the same page, combine them into a single observation.
- Set "image_id" to the corresponding image file name (e.g., "IMG_123.png") from the EXTRACTED IMAGES CONTEXT list, or "null" if no matching image is found. If multiple images apply, use a comma-separated string of filenames.
- Be concise and extract only unique physical findings.
- Keep descriptions brief (1 sentence max).
- Limit output to at most 15 observations.

Return the list of raw observations in a structured JSON list of objects:
[
  {{
    "area": "name of area",
    "defect": "type of defect",
    "description": "text description",
    "source_document": "Inspection Report or Thermal Report",
    "page_number": int,
    "image_id": "string of filenames or null"
  }}
]
"""

# ==========================================
# Stage 2: Grouping by Area
# ==========================================
STAGE_2_GROUP_BY_AREA = """
Below is a list of extracted raw observations:
{raw_observations}

Task:
Group these observations logically by property area. Return a JSON object where the keys are the names of the areas (e.g., "Bathroom", "Roof", "Kitchen") and the values are lists of observations belonging to that area.

Format:
{{
  "Area Name": [
    {{
      "defect": "type of defect",
      "description": "text description",
      "source_document": "...",
      "page_number": int,
      "image_id": "..."
    }}
  ]
}}
"""

# ==========================================
# Stage 3: Merge Duplicates
# ==========================================
STAGE_3_MERGE_DUPLICATES = """
Below is a list of grouped observations by area:
{grouped_observations}

Task:
Identify and merge duplicate observations in each area.
A duplicate is when the visual report and the thermal report (or multiple pages in the same report) describe the same physical issue.
For example, if the visual report mentions "dampness on the bathroom ceiling" and the thermal report mentions a "cold moisture anomaly on the bathroom ceiling", combine them into a single observation.

Merged observations must:
1. Combine the visual description and thermal readings into a stronger, coherent description.
2. Link ALL associated evidence sources (e.g., source document, page number, image ID) into a list.
3. Be assigned a unique ID (e.g., "OBS-001", "OBS-002").

Return the list of consolidated observations in JSON format.
"""

# ==========================================
# Stage 4: Conflict Detection
# ==========================================
STAGE_4_DETECT_CONFLICTS = """
Below is a list of consolidated observations:
{consolidated_observations}

Task:
Analyze the observations to detect conflicts.
A conflict occurs when reports or observations disagree on the severity or extent of a defect.
Example: Visual inspection indicates "minor surface dampness" but thermal scan indicates "extensive internal water accumulation."

For each observation:
1. Determine if a conflict exists between the visual findings and the thermal scan.
2. If yes, set "is_conflict" to true and provide "conflict_details" explaining the mismatch.
3. If no, set "is_conflict" to false and "conflict_details" to null.

Return the updated list of observations with conflict flags and details in JSON format.
"""

# ==========================================
# Stage 5: Infer Probable Root Cause
# ==========================================
STAGE_5_INFER_ROOT_CAUSES = """
Below is the list of observations:
{observations_with_conflicts}

Task:
For each observation, infer the probable engineering root cause.
Root causes must be derived logically from the evidence. Examples:
- Roof waterproofing failure
- Pipe leakage
- Tile joint failure
- Poor drainage
- Condensation
- Structural cracks
- Exterior wall cracks
- Sealant failure
- Parapet deterioration
- Membrane failure
- Concrete deterioration
- Corrosion

If the evidence is insufficient to determine a root cause, write "Not Available".
Return the observations with the added "probable_root_cause" field in JSON format.
"""

# ==========================================
# Stage 6: Severity and Confidence Assessment
# ==========================================
STAGE_6_SEVERITY_CONFIDENCE = """
Below is the list of observations:
{observations_with_root_causes}

Task:
For each observation, determine:
1. Severity: Low, Medium, High, Critical.
   - Critical: Immediate safety hazard, structural instability, fire risk, electrical hazard, major active leakage.
   - High: Large moisture intrusion, significant cracking, waterproofing failure, rapid deterioration.
   - Medium: Localized damage requiring repair, not immediately dangerous.
   - Low: Minor cosmetic issue, routine maintenance.
2. Reasoning: Explicitly explain WHY you assigned this severity.
3. Confidence: Low, Medium, High, Very High. Calculate strictly based on the following evidence scale:
   - Very High: Visual + Thermal + Image evidence exists.
   - High: Visual + Thermal evidence exists.
   - Medium: Visual only or Thermal only.
   - Low: Single weak/vague text observation.

Return the updated observations in JSON format.
"""

# ==========================================
# Stage 7: Recommendations Generation
# ==========================================
STAGE_7_GENERATE_RECOMMENDATIONS = """
Below is the list of assessed observations:
{assessed_observations}

Task:
Generate practical, prioritized recommendations directly relating to the defects.
Separate recommendations into:
1. "Immediate Actions" (Urgent, safety-critical, major leaks, electrical hazards).
2. "Short-term Actions" (Required within 30 days, localized repairs).
3. "Long-term Preventive Actions" (Monitoring, maintenance, waterproofing coatings).

For each recommendation, list the action type, details of what to do, and map it back to the associated observation IDs (e.g. ["OBS-001"]).
Never recommend unnecessary work.

Return the recommendations in JSON format:
[
  {{
    "priority": "Immediate Actions / Short-term Actions / Long-term Preventive Actions",
    "action_type": "Waterproofing / Plumbing / Structural / etc.",
    "description": "Detailed text of recommendation",
    "associated_observation_ids": ["OBS-001", ...]
  }}
]
"""

# ==========================================
# Stage 8: Executive Summary & Overall Risk
# ==========================================
STAGE_8_EXEC_SUMMARY = """
Below are the observations and recommendations for the property:

OBSERVATIONS:
{observations}

RECOMMENDATIONS:
{recommendations}

Task:
1. Write a professional Executive Summary in the voice of a senior engineer with 20+ years of experience. Keep it concise, authoritative, and client-friendly.
2. Formulate an overall Severity Assessment for the property:
   - "overall_severity": Overall rating ('Low', 'Medium', 'High', 'Critical').
   - "reasoning": Structural or safety rationale for this overall rating.
   - "risk_score": An integer from 0 to 100 representing the total risk profile.
   - "priority_ranking": Ranked list of property areas by urgency (highest priority first).

Return a JSON object:
{{
  "executive_summary": "summary text...",
  "overall_severity": "...",
  "reasoning": "...",
  "risk_score": int,
  "priority_ranking": ["Area A", "Area B", ...]
}}
"""

# ==========================================
# Stage 9: Final Compilation and Schema Validation
# ==========================================
STAGE_9_FINAL_COMPILATION = """
Compile the following pieces of analyzed building inspection data into a single coherent JSON structure.

PROPERTY INFO:
{property_info}

EXECUTIVE SUMMARY & SEVERITY ASSESSMENT:
{exec_summary_assessment}

OBSERVATIONS:
{observations}

RECOMMENDATIONS:
{recommendations}

MISSING INFORMATION:
Identify any missing details from the reports (e.g., moisture meter readings, roof access photos, property age, structural drawings, exact inspection dates). Return a list of missing items.

Task:
Return a single JSON payload that exactly adheres to the structure of the DDRReport Pydantic schema:
{{
  "property_info": {{
    "address": "...",
    "client_name": "...",
    "inspection_date": "..."
  }},
  "executive_summary": "...",
  "observations": [
    {{
      "id": "OBS-001",
      "area": "...",
      "defect": "...",
      "description": "...",
      "evidence": [
        {{
          "source_document": "...",
          "page_number": int,
          "image_id": "..."
        }}
      ],
      "severity": "...",
      "reasoning": "...",
      "confidence": "...",
      "probable_root_cause": "...",
      "is_conflict": bool,
      "conflict_details": "..."
    }}
  ],
  "severity_assessment": {{
    "overall_severity": "...",
    "reasoning": "...",
    "risk_score": int,
    "priority_ranking": ["...", ...]
  }},
  "recommendations": [
    {{
      "priority": "...",
      "action_type": "...",
      "description": "...",
      "associated_observation_ids": ["OBS-001", ...]
    }}
  ],
  "missing_information": [
    {{
      "item_category": "...",
      "description": "..."
    }}
  ]
}}
"""

# ==========================================
# Consolidated Stage 3-6: Engineering Analysis
# ==========================================
STAGE_3_ANALYSIS = """
Below is a list of raw observations grouped by property area:
{grouped_observations}

Task:
Perform a comprehensive engineering analysis on these grouped observations.
Specifically, you must:

1. Merge duplicates: Identify where multiple findings describe the same physical issue. Combine their descriptions into a unified engineering description (integrating visual details and thermal anomalies/temperatures). Group all their evidence sources (document name, page number, image ID) into a single "evidence" list. Assign each consolidated observation a unique ID starting from "OBS-001", "OBS-002", etc.
2. Detect conflicts: Identify if there are contradictions between the visual inspection and thermal scan (e.g. minor visual damage but major/active thermal leakage). Set "is_conflict" to true and describe the mismatch in "conflict_details". If no conflict, set "is_conflict" to false and "conflict_details" to null.
3. Infer probable root causes: Based on engineering principles, determine the likely root cause (e.g., "Roof waterproofing failure", "Pipe leakage", "Condensation"). If evidence is insufficient, use "Not Available".
4. Assess severity: Assign a severity rating ("Low", "Medium", "High", "Critical") and provide the explicit engineering reasoning.
   - Critical: Immediate safety hazard, structural instability, fire/electrical hazard, major active leakage.
   - High: Large moisture intrusion, significant cracking, waterproofing failure, rapid deterioration.
   - Medium: Localized damage requiring repair, not immediately dangerous.
   - Low: Minor cosmetic issue, routine maintenance.
5. Calculate confidence: Assign a confidence rating ("Low", "Medium", "High", "Very High") strictly using the following evidence scale:
   - Very High: Visual + Thermal + Image evidence exists.
   - High: Visual + Thermal evidence exists.
   - Medium: Visual only or Thermal only.
   - Low: Single weak/vague text observation.
6. Generate Detailed Repair Procedure: For each defect, generate a highly specific, step-by-step engineering repair procedure list of strings (e.g., ["1. Remove existing damaged grout.", "2. Remove loose plaster.", "3. Apply crystalline waterproof coating."]).
7. Estimate Cost: Estimate a realistic cost range for the repair in Indian Rupees, e.g. "₹15,000 - ₹20,000".
8. Identify Materials Required: List the specific construction/waterproofing materials required for the repair as a list of strings (e.g., ["Polymer Mortar", "Waterproof Coating", "Tile Adhesive"]).
9. Map Priority and Timeline:
   - Priority: "Critical", "High", "Medium", "Low"
   - Timeline: "Within 24 Hours", "Within 7 Days", "Within 30 Days", "Routine Maintenance"
10. Calculate Confidence Breakdown: Provide a JSON object with keys "Inspection Evidence", "Thermal Evidence", "Image Evidence", and "Overall" with corresponding percentage values (e.g. {{"Inspection Evidence": 97, "Thermal Evidence": 94, "Image Evidence": 91, "Overall": 95}}).

Return the fully analyzed observations in a JSON object matching this schema:
{{
  "observations": [
    {{
      "id": "OBS-001",
      "area": "name of area",
      "defect": "type of defect",
      "description": "unified description",
      "evidence": [
        {{
          "source_document": "Inspection Report or Thermal Report",
          "page_number": int,
          "image_id": "image code or null"
        }}
      ],
      "is_conflict": bool,
      "conflict_details": "conflict description or null",
      "probable_root_cause": "inferred cause",
      "severity": "Low/Medium/High/Critical",
      "reasoning": "severity explanation",
      "confidence": "Low/Medium/High/Very High",
      "repair_procedure": ["step 1", "step 2", ...],
      "estimated_cost": "₹15,000 - ₹20,000",
      "materials_required": ["Material A", "Material B", ...],
      "priority": "Critical/High/Medium/Low",
      "timeline": "Within 24 Hours/Within 7 Days/Within 30 Days/Routine Maintenance",
      "confidence_breakdown": {{
        "Inspection Evidence": int,
        "Thermal Evidence": int,
        "Image Evidence": int,
        "Overall": int
      }}
    }}
  ]
}}
"""

# ==========================================
# Consolidated Stage 7-9: Report Synthesis
# ==========================================
STAGE_7_SYNTHESIS = """
Compile the final Detailed Diagnostic Report (DDR) based on the analyzed observations and property details.

PROPERTY INFO:
{property_info}

ANALYZED OBSERVATIONS:
{observations}

Task:
Synthesize the entire report. Specifically, you must:

1. Generate prioritized recommendations: Formulate practical, prioritized remedies.
   Categorize them into:
   - "Immediate Actions": Urgent, safety-critical, major leaks, electrical hazards.
   - "Short-term Actions": Required within 30 days, localized repairs.
   - "Long-term Preventive Actions": Monitoring, maintenance, waterproofing coatings.
   Map each recommendation to the associated observation IDs (e.g. ["OBS-001"]).

2. Formulate executive summary: Write a professional, executive-level summary of the overall property health in the voice of a senior building diagnostics engineer with 20+ years of experience. Keep it concise, authoritative, and client-friendly.

3. Severity assessment: Determine the overall severity ("Low", "Medium", "High", "Critical"), provide the structural/safety rationale, assign an overall risk score from 0 (perfect) to 100 (immediate hazard), and rank the property areas by repair priority (highest priority first).
   - Also estimate specific building health indices (0-100%): "structural_health", "waterproofing_health", "interior_finish_health", and the "moisture_risk" rating ("Low", "Medium", "High", "Critical").

4. Identify missing information: Detail any missing documentation or measurements (e.g., moisture meter readings, roof access photos, property age, structural drawings) that affect diagnostic certainty.

5. Final Engineering Assessment: Provide a detailed, professional conclusion summarizing findings, systemic issues (e.g., waterproofing failures), and a coordinated remediation roadmap.

6. Estimated Total Cost Range: Sum or estimate the total repair cost range in Indian Rupees (e.g., "₹48,000 - ₹62,000") across all defects.

Return a single JSON payload that exactly adheres to the structure of the DDRReport schema:
{{
  "property_info": {{
    "address": "...",
    "client_name": "...",
    "inspection_date": "..."
  }},
  "executive_summary": "...",
  "observations": [
    {{
      "id": "OBS-001",
      "area": "...",
      "defect": "...",
      "description": "...",
      "evidence": [
        {{
          "source_document": "...",
          "page_number": int,
          "image_id": "..."
        }}
      ],
      "severity": "...",
      "reasoning": "...",
      "confidence": "...",
      "probable_root_cause": "...",
      "is_conflict": bool,
      "conflict_details": "...",
      "repair_procedure": ["step 1", "step 2", ...],
      "estimated_cost": "...",
      "materials_required": ["material 1", ...],
      "priority": "...",
      "timeline": "...",
      "confidence_breakdown": {{
        "Inspection Evidence": int,
        "Thermal Evidence": int,
        "Image Evidence": int,
        "Overall": int
      }}
    }}
  ],
  "severity_assessment": {{
    "overall_severity": "...",
    "reasoning": "...",
    "risk_score": int,
    "priority_ranking": ["...", ...],
    "structural_health": int,
    "waterproofing_health": int,
    "interior_finish_health": int,
    "moisture_risk": "..."
  }},
  "recommendations": [
    {{
      "priority": "Immediate Actions / Short-term Actions / Long-term Preventive Actions",
      "action_type": "Waterproofing / Plumbing / Structural / etc.",
      "description": "...",
      "associated_observation_ids": ["OBS-001", ...]
    }}
  ],
  "missing_information": [
    {{
      "item_category": "...",
      "description": "..."
    }}
  ],
  "final_engineering_assessment": "...",
  "estimated_total_cost_range": "..."
}}
"""

