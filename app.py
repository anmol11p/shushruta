# import streamlit as st
# import requests
# import base64
# import json
# import time
# from pathlib import Path
# from function import  xray_analysis,clean_and_parse_json
# from typing import Union
# import os


# #show data to user 
def extract_analysis_data(result):
    """Extract and clean analysis data from various response formats"""
    
    # If we have raw_response, try to parse it
    if result.get("raw_response"):
        cleaned_data = clean_and_parse_json(result["raw_response"])
        if cleaned_data:
            return cleaned_data
    
    # If no raw_response or parsing failed, use the result directly
    return result
def display_xray_results(data, original_result):
    """Display X-ray analysis results with clean headings and key information only"""
    
    st.subheader("📊 X-Ray Analysis Report")
    
    # Show warning if analysis wasn't successful
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
                for bone in bones[:5]:  # Show first 5
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
        
        # Fracture Detection
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
        
        # Other Abnormalities
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
        
        # Additional Findings
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
            urgency_icon = {
                'emergent': '🚨',
                'urgent': '⚠️', 
                'routine': '✅'
            }.get(urgency.lower(), '')
            st.metric("Urgency", f"{urgency_icon} {urgency.title()}")
        
        # Differential Diagnosis
        differential = assessment.get("differential_diagnosis", [])
        if differential:
            st.write("**📋 Differential Diagnosis:**")
            for i, diagnosis in enumerate(differential, 1):
                st.write(f"{i}. {diagnosis}")
        
        # Recommendations
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
    
    # Medical Disclaimer
    st.divider()
    st.warning("⚠️ **MEDICAL DISCLAIMER:** This analysis is for educational purposes only. Always consult qualified medical professionals for diagnosis and treatment.")
    
    # Technical Details (Collapsible)
    with st.expander("🔍 View Technical Details"):
        model_info = original_result.get("model_info", {})
        if model_info:
            st.write("**🤖 Model Information:**")
            st.write(f"• Model: {model_info.get('model_id', 'Unknown')}")
            st.write(f"• Max Tokens: {model_info.get('max_tokens', 'Unknown')}")
            if model_info.get('input_tokens'):
                st.write(f"• Input Tokens: {model_info['input_tokens']}")
        
        st.json(data)
def display_structured_medical_data(data):
    """Display structured medical analysis data"""
    
    # Image Metadata Section
    if "image_metadata" in data:
        st.subheader("🖼️ Image Information")
        metadata = data["image_metadata"]
        
        col1, col2 = st.columns(2)
        with col1:
            if metadata.get('side'):
                st.metric("Side", metadata['side'])
            if metadata.get('view_type'):
                st.metric("View Type", metadata['view_type'])
            if metadata.get('body_part'):
                st.metric("Body Part", metadata['body_part'])
        
        with col2:
            if metadata.get('date_taken'):
                st.metric("Date Taken", metadata['date_taken'])
            if metadata.get('patient_position'):
                st.metric("Patient Position", metadata['patient_position'])
        
        if metadata.get('technical_factors'):
            st.info(f"**Image Quality:** {metadata['technical_factors']}")
        
        st.divider()
    
    # Anatomy Section
    if "anatomy" in data:
        st.subheader("🦴 Anatomical Analysis")
        anatomy = data["anatomy"]
        
        if anatomy.get("bones_identified"):
            bones = anatomy["bones_identified"]
            
            # Filter out non-medical entries
            medical_terms = [
                bone for bone in bones 
                if bone not in ["Name", "Roll No.", "Enrol No.", "Sr. No.", "Category", "Degree", "University", "Course"]
                and len(bone.strip()) > 2
            ]
            
            if medical_terms:
                st.write("**Identified Anatomical Structures:**")
                
                # Display in columns for better layout
                if len(medical_terms) > 6:
                    col1, col2 = st.columns(2)
                    mid_point = len(medical_terms) // 2
                    
                    with col1:
                        for term in medical_terms[:mid_point]:
                            st.write(f"• {term}")
                    
                    with col2:
                        for term in medical_terms[mid_point:]:
                            st.write(f"• {term}")
                else:
                    for term in medical_terms:
                        st.write(f"• {term}")
            else:
                st.info("ℹ️ No specific anatomical structures clearly identified in this analysis.")
    
    # Findings or other sections
    if "findings" in data:
        st.subheader("🔍 Clinical Findings")
        findings = data["findings"]
        if isinstance(findings, list):
            for finding in findings:
                st.write(f"• {finding}")
        else:
            st.write(findings)
    
    if "impression" in data:
        st.subheader("💡 Clinical Impression")
        st.write(data["impression"])

def display_basic_analysis(data):
    """Display basic analysis for non-medical structured data"""
    
    # Check for common keys and display them nicely
    important_keys = ['diagnosis', 'findings', 'impression', 'recommendation', 'summary']
    
    displayed_keys = []
    for key in important_keys:
        if key in data:
            st.subheader(f"📋 {key.title()}")
            value = data[key]
            if isinstance(value, list):
                for item in value:
                    st.write(f"• {item}")
            else:
                st.write(value)
            displayed_keys.append(key)
    
    # Display any remaining keys
    remaining_data = {k: v for k, v in data.items() if k not in displayed_keys}
    if remaining_data:
        st.subheader("📊 Additional Information")
        for key, value in remaining_data.items():
            if key not in ['raw_response', 'model_info']:  # Skip technical fields
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")

# # Utility: encode uploaded image
# def encode_image(image_input: Union[str, "UploadedFile"]):
#     """
#     Encode image to base64.
#     Can take either:
#         - str path to file
#         - Streamlit UploadedFile object
#     """
#     try:
#         # Streamlit uploaded file
#         if hasattr(image_input, "read"):
#             image_data = image_input.read()
#             file_size_mb = len(image_data) / (1024 * 1024)
#         else:
#             # Local file path
#             path = Path(image_input)
#             if not path.exists():
#                 # print(f"❌ Image file not found: {image_input}")
#                 return None
#             file_size_mb = path.stat().st_size / (1024 * 1024)
#             with open(path, "rb") as f:
#                 image_data = f.read()

#         if file_size_mb > 10:
#             # print(f"⚠️ Warning: Large image file ({file_size_mb:.2f} MB)")
#             return 'file size maximum to 10mb'
#         image_base64 = base64.b64encode(image_data).decode("utf-8")
#         return image_base64

#     except Exception as e:
#         # print(f"❌ Error encoding image: {str(e)}")
#         return None
# # ------------------ Streamlit UI ------------------

# st.set_page_config(page_title="MedGemma-4B-IT X-ray Analyzer", layout="wide")

# st.title("🩻 MedGemma-4B-IT X-ray Analyzer")
# st.caption("Educational use only — not a substitute for professional medical advice.")

# # Image uploader
# uploaded_file = st.file_uploader("Upload an X-ray image (JPG/PNG)", type=["jpg", "jpeg", "png"])

# # if uploaded_file is not None:
# #     st.image(uploaded_file, caption="Uploaded X-ray", width=250)

# #     if st.button("🔬 Analyze X-ray"):
# #         with st.spinner("Analyzing..."):
# #             image_b64 = encode_image(uploaded_file)
# #             result = xray_analysis(image_b64)

# #             # Try to convert raw_response string to JSON if possible
# #             raw_data = None
# #             if result.get("raw_response"):
# #                 try:
# #                     # Strip ```json if present
# #                     raw_str = result["raw_response"].replace("```json", "").replace("```", "").strip()
# #                     raw_data = json.loads(raw_str)
# #                 except json.JSONDecodeError:
# #                     raw_data = result["raw_response"]  # fallback: keep as string

# #         st.subheader("📊 Analysis Results")

# #         # Always display the data, even if success=False
# #         if raw_data:
# #             st.json(raw_data)
# #         else:
# #             st.write(result)

# #         # Optional: show an explicit warning if success=False
# #         if result.get("success") is False:
# #             st.warning("⚠️ Analysis returned with success=False. Displaying raw data.")
# if uploaded_file is not None:
#     st.image(uploaded_file, caption="Uploaded X-ray", width=250)
    
#     if st.button("🔬 Analyze X-ray"):
#         with st.spinner("Analyzing..."):
#             image_b64 = encode_image(uploaded_file)
#             result = xray_analysis(image_b64)
            
#             if result:
#                 # Extract and clean data
#                 extracted_data = extract_analysis_data(result)
#                 display_xray_results(extracted_data, result)
#             else:
#                 st.error("❌ Failed to analyze the X-ray. Please try again.")

import streamlit as st
import json
import base64
from pathlib import Path
from typing import Union
from function import xray_analysis, clean_and_parse_json

# ---------------- Utility Functions ----------------
def encode_image(image_input: Union[str, "UploadedFile"]):
    """Encode image to base64."""
    try:
        if hasattr(image_input, "read"):  # Uploaded file
            image_data = image_input.read()
        else:  # Local file
            path = Path(image_input)
            if not path.exists():
                return None
            with open(path, "rb") as f:
                image_data = f.read()

        return base64.b64encode(image_data).decode("utf-8")
    except Exception:
        return None

def extract_analysis_data(result):
    """Extract and clean analysis data from various response formats"""
    if result.get("raw_response"):
        cleaned_data = clean_and_parse_json(result["raw_response"])
        if cleaned_data:
            return cleaned_data
    return result

def generate_markdown_report(data: dict) -> str:
    """Convert analysis results into markdown format"""
    md = "# 🩻 X-Ray Analysis Report\n\n"

    if "analysis" in data:
        analysis = data["analysis"]

        # Metadata
        metadata = analysis.get("image_metadata", {})
        if metadata:
            md += "## 📷 Image Metadata\n"
            for k, v in metadata.items():
                md += f"- **{k.replace('_',' ').title()}**: {v}\n"
            md += "\n"

        # Anatomy
        anatomy = analysis.get("anatomy", {})
        if anatomy:
            md += "## 🦴 Anatomical Structures\n"
            if anatomy.get("bones_identified"):
                md += "- **Bones Identified**: " + ", ".join(anatomy["bones_identified"]) + "\n"
            if anatomy.get("joints_in_view"):
                md += "- **Joints in View**: " + ", ".join(anatomy["joints_in_view"]) + "\n"
            md += "\n"

        # Findings
        findings = analysis.get("findings", {})
        if findings:
            md += "## 🔍 Clinical Findings\n"
            for k, v in findings.items():
                md += f"- **{k.replace('_',' ').title()}**: {v}\n"
            md += "\n"

        # Clinical Assessment
        assessment = analysis.get("clinical_assessment", {})
        if assessment:
            md += "## ⚕️ Clinical Assessment\n"
            for k, v in assessment.items():
                md += f"- **{k.replace('_',' ').title()}**: {v}\n"
            md += "\n"

    md += "\n⚠️ *Medical Disclaimer: This report is for educational purposes only.*\n"
    return md

# ---------------- Streamlit App ----------------
st.set_page_config(page_title="MedGemma-4B-IT X-ray Analyzer", layout="wide")
st.title("🩻 MedGemma-4B-IT X-ray Analyzer")
st.caption("Educational use only — not a substitute for professional medical advice.")

uploaded_file = st.file_uploader("Upload an X-ray image (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded X-ray", width=250)

    # initialize session state for results
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
        st.session_state.extracted_data = None

    if st.session_state.analysis_result is None:
        if st.button("🔬 Analyze X-ray"):
            with st.spinner("Analyzing..."):
                image_b64 = encode_image(uploaded_file)
                result = xray_analysis(image_b64)

                if result:
                    st.session_state.analysis_result = result
                    st.session_state.extracted_data = extract_analysis_data(result)
                else:
                    st.error("❌ Failed to analyze the X-ray. Please try again.")

    # show results if already analyzed
    if st.session_state.analysis_result is not None:
        extracted_data = st.session_state.extracted_data
        result = st.session_state.analysis_result

        # Display results
        display_xray_results(extracted_data, result)

        # Markdown report + download
        md_report = generate_markdown_report(extracted_data)
        st.download_button(
            label="⬇️ Download Report as Markdown",
            data=md_report,
            file_name="xray_analysis_report.md",
            mime="text/markdown"
        )
