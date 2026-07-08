import streamlit as st
import os
from pathlib import Path
import dotenv
from pydantic import ValidationError

# Load environment variables (.env file)
dotenv.load_dotenv()

# App modules
from config import (
    BASE_DIR, MAX_UPLOAD_SIZE_MB, SUPPORTED_FILE_TYPES,
    GEMINI_MODEL, LLM_PROVIDER, DEEPSEEK_MODEL
)
from logger import logger
from parser import extract_text
from image_extractor import extract_images_from_pdf
from analyzer import run_analysis_pipeline
from report_generator import generate_docx_report, generate_pdf_report
from utils import initialize_workspace, reset_project, format_file_size

# Set up Streamlit Page Configuration
st.set_page_config(
    page_title="AI DDR Report Generator",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize workspace folders at startup
initialize_workspace()

# ==========================================
# Custom Premium Dark-Mode CSS Styling
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@400;600;700;800&display=swap');

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0d1117;
    }
    ::-webkit-scrollbar-thumb {
        background: #30363d;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #00f2fe;
    }

    /* Main App Layout background */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #111827 0%, #030712 100%) !important;
        color: #e5e7eb;
        font-family: 'Inter', sans-serif;
    }

    /* Titles & Headings */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', 'Inter', sans-serif !important;
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Sleek Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #030712 !important;
        border-right: 1px solid #1f2937;
    }
    
    /* Upload areas */
    div[data-testid="stFileUploader"] {
        border: 2px dashed #00f2fe55 !important;
        background-color: #0b0f19 !important;
        border-radius: 12px !important;
        transition: all 0.3s ease-in-out;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #00f2fe !important;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.1);
    }
    
    /* Premium Glassmorphic Metric Cards */
    .premium-metrics-container {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        margin-bottom: 25px;
    }
    .premium-metric-card {
        flex: 1 1 200px;
        background: rgba(17, 24, 39, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    .premium-metric-card:hover {
        transform: translateY(-5px);
        border-color: #00f2fe99;
        box-shadow: 0 10px 25px rgba(0, 242, 254, 0.15);
    }
    .metric-icon {
        font-size: 2.2rem;
        margin-bottom: 10px;
    }
    .metric-val {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 5px;
    }
    .metric-lbl {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }

    /* Glow Observation Cards */
    .glow-card {
        background: rgba(17, 24, 39, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    
    .glow-card-critical { border-left: 6px solid #ef4444; }
    .glow-card-high { border-left: 6px solid #f97316; }
    .glow-card-medium { border-left: 6px solid #eab308; }
    .glow-card-low { border-left: 6px solid #10b981; }

    .glow-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
    }
    .glow-card-critical:hover { border-color: #ef4444; box-shadow: 0 0 20px rgba(239, 68, 68, 0.15); }
    .glow-card-high:hover { border-color: #f97316; box-shadow: 0 0 20px rgba(249, 115, 22, 0.15); }
    .glow-card-medium:hover { border-color: #eab308; box-shadow: 0 0 20px rgba(234, 179, 8, 0.15); }
    .glow-card-low:hover { border-color: #10b981; box-shadow: 0 0 20px rgba(16, 185, 129, 0.15); }

    /* Custom Status Badges */
    .pill-badge {
        display: inline-flex;
        align-items: center;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-right: 8px;
        margin-bottom: 10px;
    }
    .pill-critical { background: rgba(239, 68, 68, 0.1); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.2); }
    .pill-high { background: rgba(249, 115, 22, 0.1); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.2); }
    .pill-medium { background: rgba(234, 179, 8, 0.1); color: #fde047; border: 1px solid rgba(234, 179, 8, 0.2); }
    .pill-low { background: rgba(16, 185, 129, 0.1); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.2); }
    .pill-info { background: rgba(99, 102, 241, 0.1); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.2); }
    
    /* Interactive telemetry console style */
    .telemetry-console {
        font-family: 'Courier New', monospace;
        background: #020617 !important;
        border: 1px solid #1e293b !important;
        color: #38bdf8 !important;
        padding: 15px;
        border-radius: 8px;
        box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# Sidebar Settings and API Credentials
# ==========================================
with st.sidebar:
    st.markdown("# 🏗️")
    st.title("AI DDR Controller")
    st.caption("Building Diagnostics & Thermal Analysis Engine")
    st.markdown("---")
    
    with st.expander("⚙️ Connection & LLM Settings", expanded=False):
        st.subheader("🔑 Credentials")
        provider_sel = st.selectbox(
            "LLM Provider", 
            ["Gemini", "NVIDIA NIM (DeepSeek / MiniMax)"], 
            index=0 if os.getenv("LLM_PROVIDER", LLM_PROVIDER) == "Gemini" else 1
        )
        
        if provider_sel == "Gemini":
            os.environ["LLM_PROVIDER"] = "Gemini"
            api_key_input = st.text_input(
                "Google Gemini API Key",
                value=os.getenv("GEMINI_API_KEY", ""),
                type="password",
                help="Provide your Google Gemini API Key. Will read from .env if omitted."
            )
            if api_key_input:
                if api_key_input != os.getenv("GEMINI_API_KEY") and api_key_input != "your_gemini_api_key_here":
                    from utils import update_env_key
                    update_env_key("GEMINI_API_KEY", api_key_input)
                os.environ["GEMINI_API_KEY"] = api_key_input
        else:
            os.environ["LLM_PROVIDER"] = "DeepSeek"
            api_key_input = st.text_input(
                "NVIDIA NIM API Key",
                value=os.getenv("DEEPSEEK_API_KEY", ""),
                type="password",
                help="Provide your NVIDIA NIM API Key (e.g. nvapi-...). Will read from .env if omitted."
            )
            if api_key_input:
                if api_key_input != os.getenv("DEEPSEEK_API_KEY"):
                    from utils import update_env_key
                    update_env_key("DEEPSEEK_API_KEY", api_key_input)
                os.environ["DEEPSEEK_API_KEY"] = api_key_input
                
        st.subheader("⚙ Advanced Config")
        if provider_sel == "Gemini":
            model_options = ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
            current_model = os.getenv("GEMINI_MODEL", GEMINI_MODEL)
            if current_model in model_options:
                model_options.remove(current_model)
            model_options.insert(0, current_model)
            model_sel = st.selectbox("LLM Model Name", model_options)
            os.environ["GEMINI_MODEL"] = model_sel
        else:
            model_options = ["qwen/qwen3.5-397b-a17b", "minimaxai/minimax-m3", "deepseek-ai/deepseek-v4-flash", "deepseek-ai/deepseek-v4-pro", "minimaxai/minimax-m2.7"]
            current_model = os.getenv("DEEPSEEK_MODEL", DEEPSEEK_MODEL)
            if current_model in model_options:
                model_options.remove(current_model)
            model_options.insert(0, current_model)
            model_sel = st.selectbox("LLM Model Name", model_options)
            os.environ["DEEPSEEK_MODEL"] = model_sel
    
    st.markdown("---")
    st.subheader("📋 Property Details")
    prop_address = st.text_input("Property Address", value="123 Tech Blvd, Engineering City")
    client_name = st.text_input("Client / Owner Name", value="ACME Corp")
    inspection_date = st.text_input("Inspection Date", value="2026-07-07")
    
    st.markdown("---")
    if st.button("🔄 Reset Project Workspace", type="secondary", use_container_width=True):
        reset_project()
        st.success("Workspace reset complete!")
        st.rerun()

# ==========================================
# Main Dashboard UI Layout
# ==========================================
st.title("🏢 AI-Powered Detailed Diagnostic Report (DDR) Generator")
st.markdown("Automate native PDF text extraction, OCR, context-aware image matching, and multi-stage building diagnostic analysis.")

# Check for API Key configuration
provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER)
if provider == "Gemini" and not os.getenv("GEMINI_API_KEY"):
    st.warning("🔑 Google Gemini API Key is missing. Please add your key in the sidebar or the `.env` file to start processing.")
elif provider == "DeepSeek" and not os.getenv("DEEPSEEK_API_KEY"):
    st.warning("🔑 DeepSeek NVIDIA API Key is missing. Please add your key in the sidebar or the `.env` file to start processing.")

col_upload1, col_upload2 = st.columns(2)

with col_upload1:
    st.subheader("📄 Visual Inspection Report")
    visual_file = st.file_uploader(
        "Choose Visual Report PDF",
        type=SUPPORTED_FILE_TYPES,
        key="visual_uploader",
        help=f"Accepts PDF files up to {MAX_UPLOAD_SIZE_MB}MB"
    )

with col_upload2:
    st.subheader("🔥 Thermal Inspection Report")
    thermal_file = st.file_uploader(
        "Choose Thermal Report PDF",
        type=SUPPORTED_FILE_TYPES,
        key="thermal_uploader",
        help=f"Accepts PDF files up to {MAX_UPLOAD_SIZE_MB}MB"
    )

st.markdown("---")

# ==========================================
# Session State Initialization
# ==========================================
if "processing_done" not in st.session_state:
    st.session_state.processing_done = False
if "ddr_report" not in st.session_state:
    st.session_state.ddr_report = None
if "extracted_images" not in st.session_state:
    st.session_state.extracted_images = []
if "log_output" not in st.session_state:
    st.session_state.log_output = []

def append_ui_log(message: str) -> None:
    """Appends messages to the onscreen terminal/log container."""
    st.session_state.log_output.append(message)
    logger.info(message)

# ==========================================
# Report Processing Action Block
# ==========================================
if st.button("🚀 Generate Detailed Diagnostic Report (DDR)", type="primary", disabled=not (visual_file and thermal_file)):
    st.session_state.log_output = []
    append_ui_log("Initializing document processing pipeline...")
    
    # Setup temporary local directory paths to write uploads to
    temp_dir = BASE_DIR / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    visual_path = temp_dir / "visual_inspection_report.pdf"
    thermal_path = temp_dir / "thermal_inspection_report.pdf"
    
    try:
        # Save uploads locally to run fitz/pdf2image against them
        with open(visual_path, "wb") as f:
            f.write(visual_file.read())
        with open(thermal_path, "wb") as f:
            f.write(thermal_file.read())
            
        append_ui_log("PDF reports written locally to temp workspace.")
        
        # 1. Image Extraction Step
        append_ui_log("Step 1: Extracting images and spatial layout metadata...")
        vis_images = extract_images_from_pdf(visual_path, "Inspection Report")
        thm_images = extract_images_from_pdf(thermal_path, "Thermal Report")
        
        # Combine images
        all_images = vis_images + thm_images
        st.session_state.extracted_images = all_images
        append_ui_log(f"Extracted a total of {len(all_images)} images.")
        
        # 2. Text Extraction Step (Native + Fallback OCR)
        append_ui_log("Step 2: Parsing document text (Native text extraction & OCR fallback)...")
        visual_text = extract_text(visual_path)
        thermal_text = extract_text(thermal_path)
        
        append_ui_log(f"Inspection text length: {len(visual_text)} chars.")
        append_ui_log(f"Thermal text length: {len(thermal_text)} chars.")
        
        # 3. AI Multi-stage reasoning pipeline
        append_ui_log("Step 3: Activating multi-stage AI reasoning pipeline...")
        
        # Streamlit progress bar and label hooks
        progress_bar = st.progress(0.0)
        status_label = st.empty()
        
        def update_progress_callback(stage: int, message: str) -> None:
            progress_bar.progress(stage / 9.0)
            status_label.markdown(f"⚙ **{message}**")
            append_ui_log(f"AI Stage {stage}/9: {message}")
            
        ddr_report = run_analysis_pipeline(
            visual_text=visual_text,
            thermal_text=thermal_text,
            images_metadata=all_images,
            address=prop_address,
            client_name=client_name,
            inspection_date=inspection_date,
            progress_callback=update_progress_callback
        )
        
        st.session_state.ddr_report = ddr_report
        st.session_state.processing_done = True
        st.success("✅ AI Diagnostic analysis completed successfully!")
        
    except ValidationError as val_err:
        st.error(f"❌ Diagnostic report was generated but failed Pydantic schema validation: {str(val_err)}")
        logger.exception("Pydantic Validation failed.")
    except Exception as e:
        st.error(f"❌ Processing failed: {str(e)}")
        logger.exception("Unexpected error in pipeline.")

# ==========================================
# Post-Processing Dashboard Visualization
# ==========================================
if st.session_state.processing_done and st.session_state.ddr_report:
    ddr = st.session_state.ddr_report
    
    # 1. Premium Metrics Cards
    st.markdown(f"""
    <div class="premium-metrics-container">
        <div class="premium-metric-card">
            <div class="metric-icon">🔍</div>
            <div class="metric-lbl">Total Issues</div>
            <div class="metric-val">{len(ddr.observations)}</div>
        </div>
        <div class="premium-metric-card">
            <div class="metric-icon">🏢</div>
            <div class="metric-lbl">Overall Health</div>
            <div class="metric-val">{100 - ddr.severity_assessment.risk_score}%</div>
        </div>
        <div class="premium-metric-card">
            <div class="metric-icon">🖼️</div>
            <div class="metric-lbl">Extracted Images</div>
            <div class="metric-val">{len(st.session_state.extracted_images)}</div>
        </div>
        <div class="premium-metric-card">
            <div class="metric-icon">💰</div>
            <div class="metric-lbl">Estimated Cost</div>
            <div class="metric-val">{ddr.estimated_total_cost_range}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Building Health Indices section
    st.subheader("🏢 Detailed Building Health Indices")
    bh_col1, bh_col2, bh_col3, bh_col4 = st.columns(4)
    with bh_col1:
        st.markdown("**Structural Health**")
        st.progress(ddr.severity_assessment.structural_health / 100.0)
        st.write(f"{ddr.severity_assessment.structural_health}%")
    with bh_col2:
        st.markdown("**Waterproofing Health**")
        st.progress(ddr.severity_assessment.waterproofing_health / 100.0)
        st.write(f"{ddr.severity_assessment.waterproofing_health}%")
    with bh_col3:
        st.markdown("**Interior Finish Health**")
        st.progress(ddr.severity_assessment.interior_finish_health / 100.0)
        st.write(f"{ddr.severity_assessment.interior_finish_health}%")
    with bh_col4:
        st.markdown("**Moisture Risk Level**")
        risk_val = ddr.severity_assessment.moisture_risk
        st.markdown(f"<span class='status-badge badge-{risk_val.lower()}'>{risk_val}</span>", unsafe_allow_html=True)

    st.markdown("---")
    
    # 2. Main Dashboard columns (Content left, Charts/Telemetry right)
    col_content, col_charts = st.columns([2, 1])
    
    with col_content:
        st.subheader("📝 Executive Summary")
        st.info(ddr.executive_summary)
        
        st.subheader("🔍 Detailed Observations")
        for obs in ddr.observations:
            card_class = f"glow-card glow-card-{obs.severity.lower()}"
            pill_sev = f"pill-badge pill-{obs.severity.lower()}"
            pill_conf = f"pill-badge pill-info"
            pill_priority = f"pill-badge pill-medium"
            
            with st.container():
                st.markdown(f"""
                <div class="{card_class}">
                    <h3 style="margin-top:0px; margin-bottom:12px; background:none; -webkit-text-fill-color:inherit; color:#ffffff; font-family:'Outfit','Inter',sans-serif; font-size:1.3rem;">{obs.id} {obs.area} - {obs.defect}</h3>
                    <div>
                        <span class="{pill_sev}">Severity: {obs.severity}</span>
                        <span class="{pill_conf}">Confidence: {obs.confidence}</span>
                        <span class="{pill_priority}">Priority: {obs.priority} ({obs.timeline})</span>
                    </div>
                    <p style="margin-top:12px; margin-bottom:8px; line-height:1.6; font-size:0.95rem;"><b>Description:</b> {obs.description}</p>
                    <p style="margin-top:0px; margin-bottom:8px; line-height:1.6; font-size:0.95rem;"><b>Probable Root Cause:</b> {obs.probable_root_cause}</p>
                    <p style="margin-top:0px; margin-bottom:0px; font-weight:600; color:#00f2fe; font-size:0.95rem;">Estimated Cost: {obs.estimated_cost}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Show conflicts if highlighted
                if obs.is_conflict:
                    st.warning(f"⚡ **Conflict Identified**: {obs.conflict_details}")
                
                # Show images tied to this observation
                image_ids = []
                for ev in obs.evidence:
                    if ev.image_id:
                        for code in ev.image_id.split(','):
                            code_clean = code.strip()
                            if code_clean and code_clean not in image_ids:
                                image_ids.append(code_clean)
                
                if image_ids:
                    st.markdown("**📸 Evidence Images**")
                    cols = st.columns(min(len(image_ids), 2))
                    for idx, img_id in enumerate(image_ids):
                        matching_img = next((img for img in st.session_state.extracted_images if img.get("image_id") == img_id), None)
                        if matching_img:
                            with cols[idx % len(cols)]:
                                st.image(matching_img.get("path"), caption=f"Evidence {img_id}", use_container_width=True)
                
                # Detailed Repair Procedure
                st.markdown("**🛠 Sequential Repair Procedure**")
                for step in obs.repair_procedure:
                    st.markdown(f"- {step}")
                
                # Materials Required
                materials_joined = ", ".join([f"`{m}`" for m in obs.materials_required])
                st.markdown(f"**Materials Required:** {materials_joined}")
                
                # Confidence Breakdown
                st.markdown("**🎯 AI Confidence Telemetry**")
                conf_cols = st.columns(len(obs.confidence_breakdown.keys()))
                for idx, (source, pct) in enumerate(obs.confidence_breakdown.items()):
                    with conf_cols[idx]:
                        st.metric(source, f"{pct}%")
                
                # Evidence references
                st.markdown("**📋 Evidence Traceability**")
                for ev in obs.evidence:
                    st.caption(f"📄 {ev.source_document} - Page {ev.page_number} (Image reference: {ev.image_id or 'None'})")
                
                st.markdown("---")
                
        st.subheader("🧱 Final Engineering Assessment & Remediation Roadmap")
        st.success(ddr.final_engineering_assessment)
        
        st.subheader("🛠 Prioritized Corrective Actions")
        rec_tabs = st.tabs(["Immediate Actions", "Short-term Actions", "Long-term Preventive Actions"])
        
        priorities = ["Immediate Actions", "Short-term Actions", "Long-term Preventive Actions"]
        for tab, priority in zip(rec_tabs, priorities):
            with tab:
                recs = [r for r in ddr.recommendations if r.priority == priority]
                if not recs:
                    st.write("No corrective steps needed in this priority tier.")
                else:
                    for rec in recs:
                        st.markdown(f"- **[{rec.action_type}]** {rec.description} *(Addresses: {', '.join(rec.associated_observation_ids)})*")
                        
        st.subheader("❓ Missing or Unclear Information")
        if not ddr.missing_information:
            st.write("No missing documentation or metrics identified.")
        else:
            for item in ddr.missing_information:
                st.markdown(f"📌 **{item.item_category}**: {item.description}")
                
    with col_charts:
        st.subheader("📊 Severity Breakdown")
        severities = [obs.severity for obs in ddr.observations]
        sev_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for s in severities:
            if s in sev_counts:
                sev_counts[s] += 1
        st.bar_chart(sev_counts)
        
        st.subheader("💰 Estimated Cost Breakdown")
        cost_data = []
        for obs in ddr.observations:
            cost_data.append({
                "Area": obs.area,
                "Defect": obs.defect,
                "Estimated Cost": obs.estimated_cost
            })
        st.table(cost_data)
        st.markdown(f"**Total Cost Range:** `{ddr.estimated_total_cost_range}`")
        
        st.subheader("🎯 Priority Area Rankings")
        st.table(ddr.severity_assessment.priority_ranking)
        
        # Log console box
        st.subheader("💻 System Logs")
        with st.expander("Show processing telemetry logs", expanded=False):
            st.text_area("Pipeline Logs", value="\n".join(st.session_state.log_output), height=300)
            
        # Download modules
        st.subheader("📥 Export Final DDR")
        
        # Run report generation in background to build DOCX/PDF
        with st.spinner("Compiling reports for download..."):
            docx_report_path = generate_docx_report(ddr, st.session_state.extracted_images)
            pdf_report_path = generate_pdf_report(ddr, st.session_state.extracted_images)
            
        # DOCX Download
        if docx_report_path.exists():
            with open(docx_report_path, "rb") as docx_file:
                st.download_button(
                    label="📄 Download DOCX Report",
                    data=docx_file.read(),
                    file_name=f"DDR_{prop_address.replace(' ', '_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
                
        # PDF Download
        if pdf_report_path.exists():
            with open(pdf_report_path, "rb") as pdf_file:
                st.download_button(
                    label="📄 Download PDF Report",
                    data=pdf_file.read(),
                    file_name=f"DDR_{prop_address.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
# ==========================================
# Raw Upload State Sidebar Gallery
# ==========================================
if st.session_state.extracted_images:
    with st.expander("🖼 Extracted Image Gallery", expanded=False):
        cols = st.columns(4)
        for idx, img in enumerate(st.session_state.extracted_images):
            col = cols[idx % 4]
            with col:
                st.image(img.get("path"), caption=f"{img.get('image_id')} (Pg {img.get('page_number')})", use_container_width=True)
                st.caption(f"Source: {img.get('source_document')}")
