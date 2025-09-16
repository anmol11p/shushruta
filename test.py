"""
Updated test client for MedGemma-4B-IT X-ray analyzer on Modal
Optimized for the corrected deployment using proper multimodal model
"""

import base64
import json
import requests
import time
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# Update with your actual endpoint URLs after deployment
DEFAULT_ENDPOINT = "https://satyammishra0402--medgemma-xray-analyzer-analyze-xray-endpoint.modal.run"
HEALTH_ENDPOINT = "https://satyammishra0402--medgemma-xray-analyzer-health-check.modal.run"

class MedGemmaTestClient:
    """Test client for MedGemma-4B-IT X-ray analyzer"""
    
    def __init__(self, endpoint_url: str = DEFAULT_ENDPOINT):
        self.endpoint_url = endpoint_url
        self.health_url = endpoint_url.replace("analyze-xray-endpoint", "health-check")
        
        print(f"Using endpoint: {self.endpoint_url}")
        print(f"Health check: {self.health_url}")
        
    def check_health(self) -> bool:
        """Check if the service is healthy"""
        try:
            print("Checking service health...")
            response = requests.get(self.health_url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Service is healthy!")
                print(f"   Model: {data.get('model', 'Unknown')}")
                print(f"   Version: {data.get('version', 'Unknown')}")
                print(f"   Type: {data.get('model_type', 'Unknown')}")
                return True
            else:
                print(f"❌ Health check failed with status: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
            return False
    
    def encode_image(self, image_path: str) -> Optional[str]:
        """Encode image file to base64"""
        try:
            path = Path(image_path)
            
            if not path.exists():
                print(f"❌Image file not found: {image_path}")
                return None
            
            # Check file size
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > 10:
                print(f"⚠️ Warning: Large image file ({file_size_mb:.2f} MB)")
            
            # Read and encode image
            with open(path, 'rb') as f:
                image_data = f.read()
                
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            print(f"✅ Image encoded successfully ({file_size_mb:.2f} MB)")
            return image_base64
            
        except Exception as e:
            print(f"❌ Error encoding image: {str(e)}")
            return None
    
    def analyze_xray(
        self, 
        image_path: str,
        max_tokens: int = 1024,      # Reduced default for faster response
        custom_prompt: str = None,   # New parameter for custom prompts
        timeout: int = 180           # 3 minute timeout
    ) -> Optional[Dict[str, Any]]:
        """Send X-ray image for analysis"""
        
        print(f"\n🔬 Analyzing X-ray image: {image_path}")
        print(f"   Parameters: max_tokens={max_tokens}, timeout={timeout}s")
        
        # Encode image
        image_base64 = self.encode_image(image_path)
        if not image_base64:
            return None
        
        # Prepare request
        request_data = {
            "image": image_base64,
            "max_tokens": max_tokens
        }
        
        if custom_prompt:
            request_data["custom_prompt"] = custom_prompt
            print(f"   Using custom prompt: {custom_prompt[:100]}...")
        
        # Send request
        print(f"\n📤 Sending request...")
        start_time = time.time()
        
        try:
            response = requests.post(
                self.endpoint_url,
                json=request_data,
                timeout=timeout
            )
            
            elapsed_time = time.time() - start_time
            print(f"⏱️ Response received in {elapsed_time:.2f} seconds")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    print("✅ Analysis successful!")
                    return result
                else:
                    print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                    print(f"   Error type: {result.get('error_type', 'Unknown')}")
                    
                    if result.get('raw_response'):
                        print(f"\n📝 Raw model response (first 300 chars):")
                        print(result['raw_response'][:300])
                    
                    return result
            else:
                print(f"❌ Request failed with status code: {response.status_code}")
                print(f"   Response: {response.text[:300]}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"❌ Request timed out after {elapsed_time:.2f} seconds")
            print("   Try reducing max_tokens or check if the service is overloaded")
            return None
        except Exception as e:
            print(f"❌ Request error: {str(e)}")
            return None
    
    def display_analysis(self, result: Dict[str, Any]):
        """Display analysis results in a formatted way"""
        
        if not result or not result.get("success"):
            print("\n❌ No successful analysis to display")
            return
        
        analysis = result.get("analysis", {})
        
        print("\n" + "="*60)
        print("📊 MEDGEMMA X-RAY ANALYSIS REPORT")
        print("="*60)
        
        # Image Metadata
        metadata = analysis.get("image_metadata", {})
        if metadata:
            print("\n📷 IMAGE METADATA:")
            print(f"   • Body Part: {metadata.get('body_part', 'Unknown')}")
            print(f"   • View Type: {metadata.get('view_type', 'Unknown')}")
            print(f"   • Side: {metadata.get('side', 'Unknown')}")
            if metadata.get('side_marker') and metadata['side_marker'] != 'None':
                print(f"   • Side Marker: {metadata['side_marker']}")
        
        # Anatomy
        anatomy = analysis.get("anatomy", {})
        if anatomy:
            print("\n🦴 ANATOMICAL STRUCTURES:")
            bones = anatomy.get("bones_identified", [])
            if bones:
                print(f"   • Bones: {', '.join(bones)}")
            joints = anatomy.get("joints_in_view", [])
            if joints:
                print(f"   • Joints: {', '.join(joints)}")
            print(f"   • Soft Tissues Evaluated: {'Yes' if anatomy.get('soft_tissues_evaluated') else 'No'}")
        
        # Findings
        findings = analysis.get("findings", {})
        if findings:
            print("\n🔍 CLINICAL FINDINGS:")
            
            # Fractures
            if findings.get("fracture_detected"):
                print("   🚨 FRACTURE DETECTED!")
                fracture_details = findings.get("fracture_details", [])
                for i, fracture in enumerate(fracture_details, 1):
                    print(f"\n   Fracture #{i}:")
                    print(f"      • Bone: {fracture.get('bone_name', 'Unknown')}")
                    print(f"      • Location: {fracture.get('location_on_bone', 'Unknown')}")
                    print(f"      • Type: {fracture.get('type_of_fracture', 'Unknown')}")
                    print(f"      • Displacement: {fracture.get('displacement', 'Unknown')}")
                    if fracture.get('angulation') and fracture['angulation'] != 'None':
                        print(f"      • Angulation: {fracture['angulation']}")
                    print(f"      • Joint Surface: {'Involved' if fracture.get('involves_joint_surface') else 'Not involved'}")
                    print(f"      • Open Fracture: {'Yes' if fracture.get('open_fracture') else 'No'}")
            else:
                print("   ✅ No fractures detected")
            
            # Other abnormalities
            other_abnormalities = findings.get("other_abnormalities", [])
            if other_abnormalities:
                print("\n   Other Findings:")
                for abnormality in other_abnormalities:
                    print(f"      • {abnormality.get('type', 'Unknown')}: {abnormality.get('description', '')}")
                    if abnormality.get('location'):
                        print(f"        Location: {abnormality['location']}")
            
            # Additional findings
            if findings.get('bone_density'):
                print(f"\n   • Bone Density: {findings['bone_density']}")
            
            degenerative = findings.get("degenerative_changes", [])
            if degenerative:
                print(f"   • Degenerative Changes: {', '.join(degenerative)}")
        
        # Clinical Assessment
        assessment = analysis.get("clinical_assessment", {})
        if assessment:
            print("\n⚕️ CLINICAL ASSESSMENT:")
            severity = assessment.get('severity_level', 'Unknown')
            urgency = assessment.get('urgency', 'Unknown')
            
            # Color coding for urgency
            urgency_color = ""
            if urgency.lower() == 'emergent':
                urgency_color = "🚨 "
            elif urgency.lower() == 'urgent':
                urgency_color = "⚠️ "
            elif urgency.lower() == 'routine':
                urgency_color = "✅ "
            
            print(f"   • Severity: {severity.title()}")
            print(f"   • Urgency: {urgency_color}{urgency.title()}")
            
            differential = assessment.get("differential_diagnosis", [])
            if differential:
                print(f"\n   📋 Differential Diagnosis:")
                for i, diagnosis in enumerate(differential, 1):
                    print(f"      {i}. {diagnosis}")
            
            recommendations = assessment.get("recommendations", [])
            if recommendations:
                print(f"\n   💡 Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"      {i}. {rec}")
        
        # Technical Notes
        technical = analysis.get("technical_notes", {})
        if technical:
            print("\n📋 TECHNICAL ASSESSMENT:")
            quality = technical.get('image_quality', 'Unknown')
            print(f"   • Image Quality: {quality}")
            print(f"   • Artifacts Present: {'Yes' if technical.get('artifacts_present') else 'No'}")
            if technical.get('positioning_notes'):
                print(f"   • Positioning: {technical['positioning_notes']}")
            if technical.get('comments'):
                print(f"   • Additional Comments: {technical['comments']}")
        
        # Model Performance Info
        model_info = result.get("model_info", {})
        if model_info:
            print("\n🤖 MODEL INFORMATION:")
            print(f"   • Model: {model_info.get('model_id', 'Unknown')}")
            if model_info.get('input_tokens'):
                print(f"   • Input Tokens: {model_info['input_tokens']}")
            print(f"   • Max Tokens: {model_info.get('max_tokens', 'Unknown')}")
            print(f"   • Device: {model_info.get('device', 'Unknown')}")
        
        print("\n" + "="*60)
        print("⚠️  MEDICAL DISCLAIMER: This analysis is for educational purposes only.")
        print("   Always consult qualified medical professionals for diagnosis and treatment.")
        print("="*60)
    
    def save_result(self, result: Dict[str, Any], image_path: str):
        """Save analysis result to JSON file"""
        try:
            output_file = Path(image_path).stem + "_medgemma_analysis.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"💾 Analysis saved to: {output_file}")
            return output_file
        except Exception as e:
            print(f"❌ Failed to save result: {str(e)}")
            return None

def main():
    """Main function for running tests"""
    
    parser = argparse.ArgumentParser(description="Test MedGemma-4B-IT X-ray analyzer")
    parser.add_argument("--endpoint", type=str, default=DEFAULT_ENDPOINT,
                       help="Modal endpoint URL")
    parser.add_argument("--image", type=str,
                       help="Path to X-ray image file")
    parser.add_argument("--max-tokens", type=int, default=1024,
                       help="Maximum tokens to generate (default: 1024)")
    parser.add_argument("--timeout", type=int, default=180,
                       help="Request timeout in seconds (default: 180)")
    parser.add_argument("--custom-prompt", type=str,
                       help="Custom analysis prompt (overrides default)")
    parser.add_argument("--save", action="store_true",
                       help="Save analysis results to JSON file")
    parser.add_argument("--health", action="store_true",
                       help="Only check service health")
    
    args = parser.parse_args()
    
    # Check for placeholder URLs
    if "your-username" in args.endpoint:
        print("⚠️ Warning: Using placeholder endpoint URL.")
        print("   Please update the endpoint URL with your actual Modal deployment URL")
        print("   You can find it in the Modal dashboard after running 'modal deploy modal_app.py'")
        print()
        
        # Ask user for endpoint URL
        user_endpoint = input("Enter your endpoint URL (or press Enter to continue with placeholder): ").strip()
        if user_endpoint:
            args.endpoint = user_endpoint
        else:
            response = input("Continue with placeholder URL for testing? (y/n): ")
            if response.lower() != 'y':
                sys.exit(0)
    
    # Initialize client
    client = MedGemmaTestClient(args.endpoint)
    
    # Health check
    if args.health or (not args.image):
        if not client.check_health():
            print("\n❌ Service health check failed. Please check your deployment.")
            print("   1. Make sure you've deployed with: modal deploy modal_app.py")
            print("   2. Check the Modal dashboard for any errors")
            print("   3. Verify the endpoint URL is correct")
            sys.exit(1)
        
        if args.health:
            print("\n✅ Health check complete!")
            sys.exit(0)
    
    # Single image analysis
    if args.image:
        result = client.analyze_xray(
            args.image,
            max_tokens=args.max_tokens,
            custom_prompt=args.custom_prompt,
            timeout=args.timeout
        )
        
        if result:
            client.display_analysis(result)
            
            if args.save:
                client.save_result(result, args.image)
        
        sys.exit(0 if result and result.get("success") else 1)
    
    # No specific action
    print("\n📖 MedGemma-4B-IT X-ray Analyzer Test Client")
    print("="*50)
    print("\nUsage examples:")
    print("  python test_client.py --health                    # Check service health")
    print("  python test_client.py --image xray.jpg           # Analyze single image")
    print("  python test_client.py --image xray.jpg --save    # Save results to JSON")
    print("  python test_client.py --image xray.jpg \\")
    print("    --max-tokens 1500 --timeout 300              # Custom parameters")
    print("  python test_client.py --image xray.jpg \\")
    print("    --custom-prompt 'Focus on bone fractures'    # Custom prompt")
    print("\nBefore testing, make sure to:")
    print("  1. Deploy the model: modal deploy modal_app.py")
    print("  2. Update the endpoint URL in this script")
    print("  3. Have an X-ray image ready for testing")
    
    print(f"\nCurrent endpoint: {args.endpoint}")
    
    if "your-username" in args.endpoint:
        print("⚠️  Remember to update the endpoint URL!")

if __name__ == "__main__":
    main()