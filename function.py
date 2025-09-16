import re
import requests
import json

ANALYZE_ENDPOINT = 'https://satyammishra0402--medgemma-xray-analyzer-analyze-xray-endpoint.modal.run'
HEALTH_ENDPOINT = 'https://satyammishra0402--medgemma-xray-analyzer-health-check.modal.run'

def modelhealthy():
    try:
        response = requests.get(HEALTH_ENDPOINT.strip())
        status = response.json()
        if status['status'] == 'healthy':
            return True
        else:
            return False    
    except Exception as e:
        print(f"❌ problem in modelhealthy: {e}")
        return False


def clean_and_parse_json(raw_response):
    """Clean and parse JSON from markdown or raw string"""
    try:
        # Method 1: Try to extract content between ```json and ```
        json_pattern = r'```(?:json)?\s*(.*?)\s*```'
        match = re.search(json_pattern, raw_response, re.DOTALL)
        
        if match:
            json_str = match.group(1).strip()
        else:
            # Method 2: More aggressive cleaning
            json_str = raw_response
            # Remove various markdown patterns
            json_str = re.sub(r'```json\s*', '', json_str)
            json_str = re.sub(r'```\s*', '', json_str)
            json_str = re.sub(r'^json\s*', '', json_str, flags=re.MULTILINE)
            json_str = json_str.strip()
        
        # Additional cleaning - remove any remaining backticks
        json_str = json_str.replace('`', '').strip('\n\r\t ')
        
        # Ensure it starts with { or [
        if not (json_str.startswith('{') or json_str.startswith('[')):
            # Try to find the first { or [
            start_pos = min([pos for pos in [json_str.find('{'), json_str.find('[')] if pos != -1] or [len(json_str)])
            if start_pos < len(json_str):
                json_str = json_str[start_pos:]
        
        # Parse the cleaned JSON
        return json.loads(json_str)
        
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        # Show the problematic part for debugging
        error_pos = getattr(e, 'pos', 0)
        if error_pos < len(raw_response):
            problematic_part = raw_response[max(0, error_pos-20):error_pos+20]
            print(f"Problem around: '{problematic_part}'")
        print(f"First 100 chars of cleaned string: {json_str[:100] if 'json_str' in locals() else 'N/A'}")
        return None
    except Exception as e:
        print(f"Unexpected error in clean_and_parse_json: {e}")
        return None

def xray_analysis(image_b64):
    if modelhealthy():
        try:
            payload = {
                "image": image_b64,
                "max_tokens": 1024,
            }
            
            resp = requests.post(ANALYZE_ENDPOINT, json=payload)
            resp.raise_for_status()
            
            response_data = resp.json()
            
            # Check if the response indicates a JSON parsing error
            if not response_data.get("success", True) and response_data.get("error_type") == "json_parsing":
                raw_response = response_data.get("raw_response", "")
                if raw_response:
                    # Use the improved cleaning function
                    parsed_data = clean_and_parse_json(raw_response)
                    if parsed_data:
                        return parsed_data
                    else:
                        # If cleaning failed, return original response with error info
                        print(f'❌ Failed to clean and parse raw_response')
                        return response_data
                        
            return response_data
            
        except requests.exceptions.RequestException as e:
            print(f'❌ HTTP request error in xray_analysis: {e}')
            return {"error": f"HTTP request failed: {str(e)}"}
        except json.JSONDecodeError as e:
            print(f'❌ JSON decode error in xray_analysis: {e}')
            return {"error": f"JSON decode failed: {str(e)}"}
        except Exception as e:
            print(f'❌ Unexpected error in xray_analysis: {e}')
            return {"error": f"Unexpected error: {str(e)}"}
    else:
        return {"error": "model is not working"}