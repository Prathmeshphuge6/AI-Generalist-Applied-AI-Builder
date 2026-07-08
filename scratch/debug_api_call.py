import os
import json
import dotenv
import google.generativeai as genai
from parser import extract_text
from image_extractor import extract_images_from_pdf
from models import Stage1Response
import prompt as prompts
from config import GEMINI_MODEL, TEMPERATURE, TOP_P, MAX_OUTPUT_TOKENS

def resolve_schema_refs(schema_dict, defs):
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

def get_clean_schema(model):
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

def main():
    dotenv.load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY is not set.")
        return
        
    genai.configure(api_key=api_key)
    
    visual_path = "temp/visual_inspection_report.pdf"
    thermal_path = "temp/thermal_inspection_report.pdf"
    
    if not os.path.exists(visual_path) or not os.path.exists(thermal_path):
        print("Temp PDF files not found.")
        return
        
    print("Extracting images and text...")
    vis_images = extract_images_from_pdf(visual_path, "Inspection Report")
    thm_images = extract_images_from_pdf(thermal_path, "Thermal Report")
    all_images = vis_images + thm_images
    
    visual_text = extract_text(visual_path)
    thermal_text = extract_text(thermal_path)
    
    print(f"Visual text length: {len(visual_text)} chars")
    print(f"Thermal text length: {len(thermal_text)} chars")
    
    images_ctx_str = json.dumps(all_images, indent=2)
    s1_prompt = prompts.STAGE_1_EXTRACT_OBS.format(
        visual_text=visual_text,
        thermal_text=thermal_text,
        images_context=images_ctx_str
    )
    
    # Generate cleaned schema
    cleaned_schema = get_clean_schema(Stage1Response)
    print("Cleaned schema structure:")
    print(json.dumps(cleaned_schema, indent=2)[:500])
    
    generation_config = genai.GenerationConfig(
        temperature=TEMPERATURE,
        top_p=TOP_P,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        response_mime_type="application/json",
        response_schema=cleaned_schema
    )
    
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=prompts.SYSTEM_INSTRUCTION
    )
    
    print(f"Calling Gemini {GEMINI_MODEL} with schema...")
    response = model.generate_content(s1_prompt, generation_config=generation_config)
    
    print("\n--- Response Details ---")
    print(f"Candidates count: {len(response.candidates)}")
    if response.candidates:
        candidate = response.candidates[0]
        print(f"Finish reason: {candidate.finish_reason}")
        print(f"Safety ratings: {candidate.safety_ratings}")
        print(f"Response text length: {len(response.text)}")
        print("Response text prefix:")
        print(response.text[:500])
        print("\nResponse text suffix:")
        print(response.text[-200:])
        
if __name__ == "__main__":
    main()
