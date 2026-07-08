import sys
from pathlib import Path

# Adjust path to include DDR_AI
sys.path.append(str(Path("C:/Users/Prathamesh/.gemini/antigravity/scratch/DDR_AI")))

from parser import extract_text

visual_path = Path("C:/Users/Prathamesh/.gemini/antigravity/scratch/DDR_AI/temp/visual_inspection_report.pdf")
thermal_path = Path("C:/Users/Prathamesh/.gemini/antigravity/scratch/DDR_AI/temp/thermal_inspection_report.pdf")

output_lines = []
output_lines.append("--- VISUAL REPORT ---")
if visual_path.exists():
    vis_txt = extract_text(visual_path)
    output_lines.append(vis_txt[:1000])
else:
    output_lines.append("Visual path does not exist.")

output_lines.append("\n--- THERMAL REPORT ---")
if thermal_path.exists():
    therm_txt = extract_text(thermal_path)
    output_lines.append(therm_txt[:1000])
else:
    output_lines.append("Thermal path does not exist.")

output_path = Path("C:/Users/Prathamesh/.gemini/antigravity/scratch/DDR_AI/scratch/output.txt")
output_path.write_text("\n".join(output_lines), encoding="utf-8")
print("Done writing output.")
