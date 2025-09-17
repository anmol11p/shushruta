import streamlit as st
import json
import base64
from pathlib import Path
from typing import Union
from function import xray_analysis, clean_and_parse_json

# ---------------- Utility Functions ----------------
def extract_analysis_data(result):
    """Extract and clean analysis data from various response formats"""
    if result.get("raw_response"):
        cleaned_data = clean_and_parse_json(result["raw_response"])
        if cleaned_data:
            return cleaned_data
    return result

def display_xray_results(data, original_result):
    """Display X-ray analysis results with clean headings and key information only"""
    st.subheader("📊 X-Ray Analysis Report")

    if original_result.get("success") is False:
        st.warning("⚠️ Analysis completed with some issues.")

    analysis = data.get("analysis", {}) if isinstance(data, dict) else data

    # 📷 IMAGE METADATA
    metadata = analysis.get("image_metadata", {})
    if metadata:
        st.subheader("📷 Image Metadata")
        col1, col2, col3 = st.columns(3)
        with col1:
            if metadata.get('body_part'):
                st.metric("Body Part", metadata['body_part'])
        with col2:
            if metadata.get('view_type'):
                st.metric("View Type", metadata['view_type'])
        with col3:
            if metadata.get('side'):
                st.metric("Side", metadata['side'])
        if metadata.get('side_marker') and metadata['side_marker'] != 'None':
            st.info(f"**Side Marker:** {metadata['side_marker']}")

    # 🦴 ANATOMICAL STRUCTURES
    anatomy = analysis.get("anatomy", {})
    if anatomy:
        st.subheader("🦴 Anatomical Structures")
        col1, col2 = st.columns(2)
        with col1:
            bones = anatomy.get("bones_identified", [])
            if bones:
                st.write("**Bones Identified:**")
                for bone in bones[:5]:
                    st.write(f"• {bone}")
        with col2:
            joints = anatomy.get("joints_in_view", [])
            if joints:
                st.write("**Joints in View:**")
                for joint in joints:
                    st.write(f"• {joint}")
            soft_tissues = anatomy.get('soft_tissues_evaluated', False)
            st.metric("Soft Tissues Evaluated", "Yes" if soft_tissues else "No")

    # 🔍 CLINICAL FINDINGS
    findings = analysis.get("findings", {})
    if findings:
        st.subheader("🔍 Clinical Findings")
        if findings.get("fracture_detected"):
            st.error("🚨 **FRACTURE DETECTED!**")
            fracture_details = findings.get("fracture_details", [])
            for i, fracture in enumerate(fracture_details, 1):
                with st.expander(f"Fracture #{i} Details"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Bone:** {fracture.get('bone_name', 'Unknown')}")
                        st.write(f"**Location:** {fracture.get('location_on_bone', 'Unknown')}")
                        st.write(f"**Type:** {fracture.get('type_of_fracture', 'Unknown')}")
                    with col2:
                        st.write(f"**Displacement:** {fracture.get('displacement', 'Unknown')}")
                        if fracture.get('angulation') and fracture['angulation'] != 'None':
                            st.write(f"**Angulation:** {fracture['angulation']}")
                        st.write(f"**Joint Surface:** {'Involved' if fracture.get('involves_joint_surface') else 'Not involved'}")
                        st.write(f"**Open Fracture:** {'Yes' if fracture.get('open_fracture') else 'No'}")
        else:
            st.success("✅ **No fractures detected**")

        other_abnormalities = findings.get("other_abnormalities", [])
        if other_abnormalities:
            st.write("**Other Findings:**")
            for abnormality in other_abnormalities:
                abnorm_type = abnormality.get('type', 'Unknown')
                description = abnormality.get('description', '')
                location = abnormality.get('location', '')
                if location:
                    st.write(f"• **{abnorm_type}:** {description} (Location: {location})")
                else:
                    st.write(f"• **{abnorm_type}:** {description}")

        if findings.get('bone_density'):
            st.info(f"**Bone Density:** {findings['bone_density']}")
        degenerative = findings.get("degenerative_changes", [])
        if degenerative:
            st.info(f"**Degenerative Changes:** {', '.join(degenerative)}")

    # ⚕️ CLINICAL ASSESSMENT
    assessment = analysis.get("clinical_assessment", {})
    if assessment:
        st.subheader("⚕️ Clinical Assessment")
        col1, col2 = st.columns(2)
        with col1:
            severity = assessment.get('severity_level', 'Unknown')
            st.metric("Severity Level", severity.title())
        with col2:
            urgency = assessment.get('urgency', 'Unknown')
            urgency_icon = {'emergent': '🚨','urgent': '⚠️','routine': '✅'}.get(urgency.lower(), '')
            st.metric("Urgency", f"{urgency_icon} {urgency.title()}")
        differential = assessment.get("differential_diagnosis", [])
        if differential:
            st.write("**📋 Differential Diagnosis:**")
            for i, diagnosis in enumerate(differential, 1):
                st.write(f"{i}. {diagnosis}")
        recommendations = assessment.get("recommendations", [])
        if recommendations:
            st.write("**💡 Recommendations:**")
            for i, rec in enumerate(recommendations, 1):
                st.write(f"{i}. {rec}")

    # 📋 TECHNICAL ASSESSMENT
    technical = analysis.get("technical_notes", {})
    if technical:
        st.subheader("📋 Technical Assessment")
        quality = technical.get('image_quality', 'Unknown')
        artifacts = technical.get('artifacts_present', False)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Image Quality", quality)
        with col2:
            st.metric("Artifacts Present", "Yes" if artifacts else "No")
        if technical.get('positioning_notes'):
            st.info(f"**Positioning:** {technical['positioning_notes']}")
        if technical.get('comments'):
            st.info(f"**Comments:** {technical['comments']}")

    st.divider()
    st.warning("⚠️ **MEDICAL DISCLAIMER:** This analysis is for educational purposes only. Always consult qualified medical professionals for diagnosis and treatment.")

    with st.expander("🔍 View Technical Details"):
        model_info = original_result.get("model_info", {})
        if model_info:
            st.write("**🤖 Model Information:**")
            st.write(f"• Model: {model_info.get('model_id', 'Unknown')}")
            st.write(f"• Max Tokens: {model_info.get('max_tokens', 'Unknown')}")
            if model_info.get('input_tokens'):
                st.write(f"• Input Tokens: {model_info['input_tokens']}")
        st.json(data)

def encode_image(image_input: Union[str, "UploadedFile"]):
    """Encode image to base64."""
    try:
        if hasattr(image_input, "read"):
            image_data = image_input.read()
        else:
            path = Path(image_input)
            if not path.exists():
                return None
            with open(path, "rb") as f:
                image_data = f.read()
        return base64.b64encode(image_data).decode("utf-8")
    except Exception:
        return None

def generate_markdown_report(data: dict) -> str:
    md = "# 🩻 X-Ray Analysis Report\n\n"
    if "analysis" in data:
        analysis = data["analysis"]
        metadata = analysis.get("image_metadata", {})
        if metadata:
            md += "## 📷 Image Metadata\n"
            for k, v in metadata.items():
                md += f"- **{k.replace('_',' ').title()}**: {v}\n"
            md += "\n"
        anatomy = analysis.get("anatomy", {})
        if anatomy:
            md += "## 🦴 Anatomical Structures\n"
            if anatomy.get("bones_identified"):
                md += "- **Bones Identified**: " + ", ".join(anatomy["bones_identified"]) + "\n"
            if anatomy.get("joints_in_view"):
                md += "- **Joints in View**: " + ", ".join(anatomy["joints_in_view"]) + "\n"
            md += "\n"
        findings = analysis.get("findings", {})
        if findings:
            md += "## 🔍 Clinical Findings\n"
            for k, v in findings.items():
                md += f"- **{k.replace('_',' ').title()}**: {v}\n"
            md += "\n"
        assessment = analysis.get("clinical_assessment", {})
        if assessment:
            md += "## ⚕️ Clinical Assessment\n"
            for k, v in assessment.items():
                md += f"- **{k.replace('_',' ').title()}**: {v}\n"
            md += "\n"
    md += "\n⚠️ *Medical Disclaimer: This report is for educational purposes only.*\n"
    return md

# ---------------- Page Config ----------------
st.set_page_config(page_title="Sushruta", layout="wide")

# ---- Responsive CSS for Light/Dark Mode ----
st.markdown(
    """
    <style>
        /* Detect system theme and adjust colors accordingly */
        :root {
            --primary-color: #4CAF50;
            --primary-hover: #45a049;
            --text-primary: var(--text-color);
            --bg-primary: var(--background-color);
            --border-color: #ddd;
            --shadow-color: rgba(0,0,0,0.1);
        }

        /* Dark theme adjustments */
        @media (prefers-color-scheme: dark) {
            :root {
                --border-color: #444;
                --shadow-color: rgba(255,255,255,0.1);
            }
        }

        /* Header styling - adapts to theme */
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 15px 30px;
            border-radius: 10px;
            background: linear-gradient(135deg, var(--primary-color), #2E8B57);
            margin-bottom: 20px;
            box-shadow: 0 4px 6px var(--shadow-color);
        }
        .header h1 {
            color: white;
            margin: 0;
            font-size: 28px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        .header a {
            text-decoration: none;
            color: #FFD700;
            font-weight: bold;
            padding: 8px 16px;
            border-radius: 6px;
            background: rgba(255,255,255,0.1);
            transition: all 0.3s ease;
        }
        .header a:hover {
            background: rgba(255,255,255,0.2);
            transform: translateY(-2px);
        }

        /* File uploader styling - responsive to theme */
        div[data-testid="stFileUploader"] {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            background: transparent;
            border: 2px dashed var(--primary-color);
            border-radius: 15px;
            padding: 40px;
            margin: 20px auto;
            width: 60%;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        div[data-testid="stFileUploader"]:hover {
            border-color: var(--primary-hover);
            transform: scale(1.02);
        }

        /* Buttons - theme adaptive */
        .stButton > button, .stDownloadButton > button {
            background: var(--primary-color) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 8px 20px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 4px var(--shadow-color) !important;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            background: var(--primary-hover) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 8px var(--shadow-color) !important;
        }

        /* Cards and containers */
        .metric-container {
            background: var(--bg-primary);
            padding: 15px;
            border-radius: 10px;
            border: 1px solid var(--border-color);
            margin: 10px 0;
            box-shadow: 0 2px 4px var(--shadow-color);
        }

        /* Expandable sections */
        .streamlit-expanderHeader {
            background: var(--bg-primary) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            margin: 5px 0 !important;
        }

        /* Alerts and info boxes - theme responsive */
        .stAlert {
            border-radius: 8px !important;
            border-left: 4px solid var(--primary-color) !important;
            box-shadow: 0 2px 4px var(--shadow-color) !important;
        }

        /* Logo container */
        .logo-container {
            text-align: center;
            margin-bottom: 20px;
            padding: 15px;
            background: var(--bg-primary);

        }
        .logo-container img {
            width: 120px;
            border-radius: 8px;
            box-shadow: 0 2px 4px var(--shadow-color);
        }

        /* Responsive design */
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                text-align: center;
                gap: 10px;
            }
            .header h1 {
                font-size: 24px;
            }
            div[data-testid="stFileUploader"] {
                width: 90%;
                padding: 30px 20px;
            }
        }

        /* Additional theme-specific adjustments */
        .stMetric {
            background: var(--bg-primary);
            padding: 10px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            margin: 5px 0;
        }

        /* Sidebar styling */
        .css-1d391kg {
            background: var(--bg-primary);
            border-right: 1px solid var(--border-color);
        }

        /* Success/Error/Warning messages */
        .stSuccess {
            background: rgba(76, 175, 80, 0.1) !important;
            border: 1px solid #4CAF50 !important;
        }
        .stError {
            background: rgba(244, 67, 54, 0.1) !important;
            border: 1px solid #f44336 !important;
        }
        .stWarning {
            background: rgba(255, 193, 7, 0.1) !important;
            border: 1px solid #FFC107 !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ---- Custom Header ----
st.markdown(
    """
    <div class="header">
        <h1> Sushruta</h1>
        <a href="https://www.anktechsol.com/" target="_blank">🔗 anktechsol</a>
    </div>
    """,
    unsafe_allow_html=True
)

# ---- Description Section ----
with st.expander("ℹ️ About Sushruta"):
    st.markdown(
        """
        ### About Sushruta
        
        **Sushruta** is an AI-powered medical imaging analysis tool that provides structured X-ray analysis for educational purposes.
        
        **Key Features:**
        - 🔍 **Anatomical Structure Identification** - Identifies bones, joints, and soft tissues
        - 🚨 **Fracture Detection** - Detects and analyzes fractures with detailed information
        - 📋 **Clinical Assessment** - Provides severity levels and clinical recommendations
        - 📄 **Downloadable Reports** - Generate detailed markdown reports
        - 🎨 **Responsive Design** - Works seamlessly in both light and dark themes
        
        **Important:** This tool is for educational and demonstration purposes only. Always consult qualified medical professionals for actual diagnosis and treatment.
        """,
    )

# ---- Sidebar Branding & Info ----
with st.sidebar:
    st.markdown(
        
        """
        <style>
        .logo-container{
        border:none;
        mix-blend-mode:multiply;
        }
        </style>
        <div class="logo-container">
            <img src="https://media.licdn.com/dms/image/v2/D560BAQHjQTh95pHYew/company-logo_200_200/B56Zc7XyPZHoAI-/0/1749047782704/ank_techsol_logo?e=1761177600&v=beta&t=FhD85Q7ZLxvd6343EWHMscoAaDuAM3jot5QkQEjgrrY">
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("### ⚡ Powered by [anktechsol](https://www.anktechsol.com/)")
    
    st.info("📌 **How to Use:**\n1. Upload an X-ray image\n2. Click 'Analyze X-ray'\n3. View detailed results\n4. Download the report")
    
    st.warning("⚠️ **Disclaimer:** For educational/demo purposes only. Not for clinical decision-making.")

# ---- Main Content Area ----
st.markdown("### 📤 Upload X-ray Image")

# File uploader
uploaded_file = st.file_uploader(
    "Choose an X-ray image file", 
    type=["jpg", "jpeg", "png"],
    help="Supported formats: JPG, JPEG, PNG. Maximum file size: 200MB"
)

if uploaded_file is not None:
    # Display uploaded image
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(uploaded_file, caption="✅ Uploaded X-ray Image", use_container_width=True)
    
    # Initialize session state
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
        st.session_state.extracted_data = None

    # Analysis button and logic
    if st.session_state.analysis_result is None:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔬 Analyze X-ray", use_container_width=True, type="primary"):
                with st.spinner("⏳ Analyzing X-ray image... This may take a moment."):
                    image_b64 = encode_image(uploaded_file)
                    if image_b64:
                        result = xray_analysis(image_b64)
                        if result:
                            st.session_state.analysis_result = result
                            st.session_state.extracted_data = extract_analysis_data(result)
                            st.rerun()
                        else:
                            st.error("❌ Failed to analyze the X-ray. Please try again.")
                    else:
                        st.error("❌ Failed to process the uploaded image. Please try again.")
    
    # Display results if analysis is complete
    if st.session_state.analysis_result is not None:
        extracted_data = st.session_state.extracted_data
        result = st.session_state.analysis_result

        # Success message
        st.success("✅ Analysis Complete!")
        
        # Create layout for results and download
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Display main analysis results
            display_xray_results(extracted_data, result)
        
        with col2:
            # Download section
            st.markdown("### 📄 Export Report")
            md_report = generate_markdown_report(extracted_data)
            
            # Download button
            st.download_button(
                label="📥 Download Report",
                data=md_report,
                file_name=f"xray_analysis_report_{uploaded_file.name.split('.')[0]}.md",
                mime="text/markdown",
                use_container_width=True,
                help="Download the complete analysis report as a Markdown file"
            )
            
            # Analysis stats
            st.markdown("### 📊 Analysis Stats")
            model_info = result.get("model_info", {})
            if model_info:
                st.metric("Model Used", model_info.get('model_id', 'Unknown').split('/')[-1])
                st.metric("Tokens Used", f"{model_info.get('input_tokens', 'N/A')}")
            
            # Reset button
            st.markdown("### 🔄 Actions")
            if st.button("🆕 Analyze New Image", use_container_width=True):
                st.session_state.analysis_result = None
                st.session_state.extracted_data = None
                st.rerun()

        # Footer
        st.markdown("---")
        st.markdown(
            """
            <div style="text-align: center; padding: 20px; opacity: 0.7;">
                🔒 <strong>Privacy Notice:</strong> Images are processed securely and not stored permanently.<br>
                💡 <strong>Support:</strong> For technical support, visit <a href="https://www.anktechsol.com/" target="_blank">anktechsol.com</a>
            </div>
            """,
            unsafe_allow_html=True
        )

else:
    # Welcome message when no file is uploaded
    st.markdown(
        """
        <div style="text-align: center; padding: 40px; opacity: 0.8;">
            <h3>👋 Welcome to Sushruta</h3>
            <p>Upload an X-ray image above to get started with AI-powered medical image analysis.</p>
            <p><em>Supported formats: JPG, JPEG, PNG</em></p>
        </div>
        """,
        unsafe_allow_html=True
    )