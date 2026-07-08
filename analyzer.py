import json
import os
from typing import List, Dict, Any, Callable, Optional
import google.generativeai as genai
from pydantic import ValidationError

from config import (
    TEMPERATURE, TOP_P, MAX_OUTPUT_TOKENS,
    LLM_PROVIDER, DEEPSEEK_MODEL, DEEPSEEK_API_BASE
)
from logger import logger
import openai
from models import (
    DDRReport, Stage1Response, Stage2Response, Stage3Response,
    Stage4Response, Stage5Response, Stage6Response, Stage7Response, Stage8Response
)
import prompt as prompts

# Helper functions to convert Pydantic models to Gemini-compatible OpenAPI schemas
def resolve_schema_refs(schema_dict: Any, defs: dict) -> Any:
    if isinstance(schema_dict, dict):
        if "$ref" in schema_dict:
            ref_path = schema_dict["$ref"]
            ref_name = ref_path.split("/")[-1]
            resolved = defs.get(ref_name, {})
            resolved_copy = json.loads(json.dumps(resolved))
            return resolve_schema_refs(resolved_copy, defs)
        else:
            return {k: resolve_schema_refs(v, defs) for k, v in schema_dict.items()}
    elif isinstance(schema_dict, list):
        return [resolve_schema_refs(item, defs) for item in schema_dict]
    return schema_dict

def get_clean_schema(model: Any) -> dict:
    raw_schema = model.model_json_schema()
    defs = raw_schema.pop("$defs", {})
    resolved = resolve_schema_refs(raw_schema, defs)
    
    def clean_fields(s):
        if isinstance(s, dict):
            # Flatten union types (anyOf, oneOf, allOf) to their first non-null type
            for union_key in ["anyOf", "oneOf", "allOf"]:
                if union_key in s:
                    sub_types = s.pop(union_key)
                    non_null_type = None
                    for item in sub_types:
                        item_resolved = resolve_schema_refs(item, defs)
                        if isinstance(item_resolved, dict) and item_resolved.get("type") != "null":
                            non_null_type = item_resolved
                            break
                    if non_null_type:
                        s.update(non_null_type)
            
            s.pop("default", None)
            s.pop("title", None)
            s.pop("$schema", None)
            for k, v in list(s.items()):
                s[k] = clean_fields(v)
        elif isinstance(s, list):
            s = [clean_fields(x) for x in s]
        return s
    
    return clean_fields(resolved)

# Initialize Gemini SDK Configuration
def configure_gemini() -> bool:
    """
    Configures the google-generativeai library using the GEMINI_API_KEY environment variable.
    
    Returns:
        bool: True if configuration was successful, False otherwise.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is not set. API calls will fail.")
        return False
    
    genai.configure(api_key=api_key)
    logger.info("Gemini API configured successfully.")
    return True

def call_gemini(
    prompt_text: str, 
    system_instruction: str = prompts.SYSTEM_INSTRUCTION, 
    json_mode: bool = True,
    schema: Optional[Any] = None,
    max_tokens: Optional[int] = None
) -> str:
    """
    Makes a call to the configured Gemini model with automatic retry and model fallback.
    """
    import time
    
    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY environment variable is missing. Cannot make API call.")

    effective_max_tokens = max_tokens if max_tokens is not None else MAX_OUTPUT_TOKENS
    primary_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    # Fallback model chain for rate limit recovery
    fallback_models = [primary_model, "gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-8b", "gemini-2.0-flash-lite"]
    seen = set()
    model_chain = []
    for m in fallback_models:
        if m not in seen:
            seen.add(m)
            model_chain.append(m)

    generation_config = genai.GenerationConfig(
        temperature=TEMPERATURE,
        top_p=TOP_P,
        max_output_tokens=effective_max_tokens,
        response_mime_type="application/json" if json_mode else "text/plain",
        response_schema=get_clean_schema(schema) if (json_mode and schema) else None
    )
    
    last_error = None
    for model_name in model_chain:
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction
        )
        
        for attempt in range(2):
            try:
                logger.debug(f"Calling Gemini ({model_name}) attempt {attempt+1} with prompt length: {len(prompt_text)}")
                response = model.generate_content(prompt_text, generation_config=generation_config)
                
                if response.candidates:
                    finish_reason = response.candidates[0].finish_reason
                    logger.debug(f"Gemini finish_reason: {finish_reason}")
                    if finish_reason == 2:
                        logger.warning("Gemini response was TRUNCATED due to max_output_tokens limit.")
                
                if not response.text:
                    logger.error("Received empty response from Gemini model.")
                    raise ValueError("Received empty response from Gemini model.")
                    
                logger.debug(f"Gemini response character length: {len(response.text)}")
                return response.text.strip()
                
            except Exception as e:
                last_error = e
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                    wait_time = (attempt + 1) * 30
                    logger.warning(f"Rate limited on {model_name} (attempt {attempt+1}). Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Non-retryable error on {model_name}: {error_str}")
                    break
        
        logger.warning(f"All retries exhausted for {model_name}. Trying next fallback model...")
    
    raise ValueError(f"All models and retries exhausted. Last error: {last_error}")

def call_deepseek(
    prompt_text: str, 
    system_instruction: str = prompts.SYSTEM_INSTRUCTION, 
    json_mode: bool = True,
    max_tokens: Optional[int] = None
) -> str:
    """
    Calls NVIDIA NIM DeepSeek models using OpenAI-compatible SDK.
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable is missing. Cannot make API call to DeepSeek.")
    if api_key.startswith("Bearer "):
        api_key = api_key[7:].strip()
        
    base_url = os.getenv("DEEPSEEK_API_BASE", DEEPSEEK_API_BASE)
    model_name = os.getenv("DEEPSEEK_MODEL", DEEPSEEK_MODEL)
    
    default_max = 16384 if "qwen" in model_name.lower() else 4096
    effective_max_tokens = max_tokens if max_tokens is not None else default_max
    
    client = openai.OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": prompt_text}
    ]
    
    logger.debug(f"Calling DeepSeek ({model_name}) with prompt length: {len(prompt_text)}")
    
    kwargs = {
        "model": model_name,
        "messages": messages,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "max_tokens": effective_max_tokens
    }
    
    if json_mode and "minimax" not in model_name.lower() and "qwen" not in model_name.lower():
        kwargs["response_format"] = {"type": "json_object"}
        
    response = client.chat.completions.create(**kwargs)
    
    # Safely handle choices list being empty or populated
    if not response.choices:
        logger.error(f"NVIDIA NIM response returned no choices: {response}")
        raise ValueError("Received empty choices from NVIDIA NIM model.")
        
    content = response.choices[0].message.content
    
    if not content:
        logger.error("Received empty content from NVIDIA NIM model choices.")
        raise ValueError("Received empty content from NVIDIA NIM model choices.")
        
    logger.debug(f"DeepSeek response character length: {len(content)}")
    return content.strip()

def call_llm(
    prompt_text: str, 
    system_instruction: str = prompts.SYSTEM_INSTRUCTION, 
    json_mode: bool = True,
    schema: Optional[Any] = None,
    max_tokens: Optional[int] = None
) -> str:
    """
    Routes LLM call based on LLM_PROVIDER config (Gemini vs. DeepSeek).
    """
    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER)
    if provider == "DeepSeek":
        return call_deepseek(prompt_text, system_instruction, json_mode, max_tokens)
    else:
        return call_gemini(prompt_text, system_instruction, json_mode, schema, max_tokens)

def repair_truncated_json(json_str: str) -> Any:
    """
    Attempts to repair a truncated JSON string (e.g., cut off by max_output_tokens).
    Works by closing any open strings, arrays, and objects from the truncation point.
    """
    logger.info("Attempting to repair truncated JSON...")
    s = json_str.rstrip()
    
    last_complete_obj = s.rfind('},')
    last_complete_obj2 = s.rfind('}]')
    
    best_cut = max(last_complete_obj, last_complete_obj2)
    
    if last_complete_obj > last_complete_obj2:
        repaired = s[:last_complete_obj + 1]
        open_brackets = repaired.count('[') - repaired.count(']')
        open_braces = repaired.count('{') - repaired.count('}')
        
        repaired += ']' * open_brackets
        repaired += '}' * open_braces
        
        try:
            result = json.loads(repaired)
            logger.info(f"JSON repair successful! Salvaged partial data.")
            return result
        except json.JSONDecodeError:
            pass
    
    for i in range(len(s) - 1, 0, -1):
        if s[i] == '}':
            candidate = s[:i+1]
            open_brackets = candidate.count('[') - candidate.count(']')
            open_braces = candidate.count('{') - candidate.count('}')
            candidate += ']' * open_brackets
            candidate += '}' * open_braces
            try:
                result = json.loads(candidate)
                logger.info(f"JSON repair successful via fallback! Salvaged partial data.")
                return result
            except json.JSONDecodeError:
                continue
    
    logger.error("JSON repair failed - could not salvage any data.")
    return None

def extract_json_substring(s: str) -> str:
    """
    Finds and extracts the first valid JSON array or object block inside a string.
    """
    first_brace = s.find('{')
    first_bracket = s.find('[')
    
    start_idx = -1
    if first_brace != -1 and first_bracket != -1:
        start_idx = min(first_brace, first_bracket)
    elif first_brace != -1:
        start_idx = first_brace
    elif first_bracket != -1:
        start_idx = first_bracket
        
    if start_idx == -1:
        return s
        
    last_brace = s.rfind('}')
    last_bracket = s.rfind(']')
    
    end_idx = max(last_brace, last_bracket)
    if end_idx == -1 or end_idx < start_idx:
        return s
        
    return s[start_idx:end_idx + 1]

def safe_parse_json(json_str: str) -> Any:
    """
    Attempts to safely parse JSON from a string, with minor cleanups.
    Falls back to truncated JSON repair if standard parsing fails.
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass
        
    cleaned = json_str.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    
    extracted = extract_json_substring(cleaned)
    
    try:
        return json.loads(extracted)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON substring parse failed: {str(e)}. Attempting truncated JSON repair...")
        
        repaired = repair_truncated_json(extracted)
        if repaired is not None:
            return repaired
            
        logger.error(f"All JSON parse attempts failed. Raw string: {json_str[:500]}...")
        raise e

def run_analysis_pipeline(
    visual_text: str,
    thermal_text: str,
    images_metadata: List[Dict[str, Any]],
    address: str = "Not Available",
    client_name: str = "Not Available",
    inspection_date: str = "Not Available",
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> DDRReport:
    """
    Runs the 9-stage building diagnostics analysis pipeline using Gemini.
    
    Args:
        visual_text (str): Native/OCR text from visual report.
        thermal_text (str): Native/OCR text from thermal report.
        images_metadata (List[Dict[str, Any]]): Extracted image metadata list.
        address (str): Property address.
        client_name (str): Client/Owner name.
        inspection_date (str): Date of inspection.
        progress_callback (Callable): Callback tracking (stage_number, stage_description).
        
    Returns:
        DDRReport: Verified Pydantic report model.
    """
    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER)
    if provider == "Gemini":
        configure_gemini()
    
    logger.info("Initializing multi-stage AI Diagnostics Pipeline...")
    
    # ----------------------------------------------------
    # Stage 1: Raw Observation Extraction (API Call 1)
    # ----------------------------------------------------
    if progress_callback:
        progress_callback(1, "Stage 1/9: Extracting raw observations from reports...")
        
    images_ctx_str = json.dumps(images_metadata, indent=2)
    s1_prompt = prompts.STAGE_1_EXTRACT_OBS.format(
        visual_text=visual_text,
        thermal_text=thermal_text,
        images_context=images_ctx_str
    )
    s1_raw = call_llm(s1_prompt)  # No schema constraint - let the model be concise
    s1_json = safe_parse_json(s1_raw)
    # Handle both {"observations": [...]} and bare [...] formats
    if isinstance(s1_json, list):
        s1_parsed = s1_json
    else:
        s1_parsed = s1_json.get("observations", [])
    logger.info(f"Stage 1 complete. Extracted {len(s1_parsed)} raw observations.")

    if not s1_parsed:
        logger.error("Stage 1 produced zero observations. Cannot continue pipeline.")
        raise ValueError("Stage 1 extraction failed: No observations could be extracted from the reports. The API response may have been too short. Please try again.")

    # ----------------------------------------------------
    # Stage 2: Grouping by Area (Local Python logic)
    # ----------------------------------------------------
    if progress_callback:
        progress_callback(2, "Stage 2/9: Grouping observations by property areas...")
        
    # Group locally in Python
    s2_parsed = {}
    for obs in s1_parsed:
        area = obs.get("area", "Other")
        cleaned_obs = {
            "defect": obs.get("defect", "Not Available"),
            "description": obs.get("description", "Not Available"),
            "source_document": obs.get("source_document", "Not Available"),
            "page_number": obs.get("page_number", 1),
            "image_id": obs.get("image_id", None)
        }
        s2_parsed.setdefault(area, []).append(cleaned_obs)
    logger.info(f"Stage 2 complete. Grouped observations into {len(s2_parsed.keys())} areas.")

    # ----------------------------------------------------
    # Stage 3: Merge Duplicates, Conflicts, Root Causes, Severities (API Call 2)
    # ----------------------------------------------------
    if progress_callback:
        progress_callback(3, "Stage 3/9: Detecting and merging duplicate findings...")
        
    s3_prompt = prompts.STAGE_3_ANALYSIS.format(
        grouped_observations=json.dumps(s2_parsed, indent=2)
    )
    s3_raw = call_llm(s3_prompt, schema=Stage6Response)
    s6_parsed = safe_parse_json(s3_raw).get("observations", [])
    logger.info(f"Consolidated and analyzed observations into {len(s6_parsed)} unique findings.")

    # ----------------------------------------------------
    # Stage 4: Conflict Detection (Reused from API Call 2)
    # ----------------------------------------------------
    if progress_callback:
        progress_callback(4, "Stage 4/9: Scanning for conflicting report data...")
    logger.info("Stage 4 complete (reused consolidated analysis).")

    # ----------------------------------------------------
    # Stage 5: Probable Root Cause Ingress (Reused from API Call 2)
    # ----------------------------------------------------
    if progress_callback:
        progress_callback(5, "Stage 5/9: Inferring probable engineering root causes...")
    logger.info("Stage 5 complete (reused consolidated analysis).")

    # ----------------------------------------------------
    # Stage 6: Severity & Confidence Mapping (Reused from API Call 2)
    # ----------------------------------------------------
    if progress_callback:
        progress_callback(6, "Stage 6/9: Assessing severities and evidence confidence...")
    logger.info("Stage 6 complete (reused consolidated analysis).")

    # ----------------------------------------------------
    # Stage 7: Recommendations, Executive Summary, Report Synthesis (API Call 3)
    # ----------------------------------------------------
    if progress_callback:
        progress_callback(7, "Stage 7/9: Generating corrective action items...")
        
    property_info_dict = {
        "address": address,
        "client_name": client_name,
        "inspection_date": inspection_date
    }
    
    s7_prompt = prompts.STAGE_7_SYNTHESIS.format(
        property_info=json.dumps(property_info_dict, indent=2),
        observations=json.dumps(s6_parsed, indent=2)
    )
    
    final_raw = call_llm(s7_prompt, schema=DDRReport)
    final_json = safe_parse_json(final_raw)
    logger.info("Stage 7 complete. Generated recommendations and report details.")

    # ----------------------------------------------------
    # Stage 8: Executive Summary & Overall Risk (Reused from API Call 3)
    # ----------------------------------------------------
    if progress_callback:
        progress_callback(8, "Stage 8/9: Drafting executive summary and overall risk rating...")
    logger.info("Stage 8 complete (reused consolidated synthesis).")

    # ----------------------------------------------------
    # Stage 9: Final Report Compilation & Pydantic Validation
    # ----------------------------------------------------
    if progress_callback:
        progress_callback(9, "Stage 9/9: Compiling final DDR and verifying Pydantic schema...")
        
    # Validate final JSON data structure using Pydantic DDRReport model
    try:
        validated_ddr = DDRReport(**final_json)
        logger.info("DDR successfully validated against Pydantic schema!")
        return validated_ddr
    except ValidationError as val_err:
        logger.critical(f"Pydantic Validation Error in compiled DDR: {val_err.json()}")
        raise val_err
