import re
import base64
import json
from typing import Any, Dict

def validate_url(url: str) -> bool:
    """Validate URL format"""
    url_pattern = re.compile(
        r'^(https?|ftp)://[^\s/$.?#].[^\s]*$', 
        re.IGNORECASE
    )
    return bool(url_pattern.match(url))

def safe_json_parse(json_string: str) -> Any:
    """Safely parse JSON string"""
    try:
        return json.loads(json_string)
    except:
        return None

def extract_json_from_text(text: str) -> Dict:
    """Extract JSON object from text"""
    json_pattern = r'\{[^{}]*\}'
    matches = re.findall(json_pattern, text)
    
    for match in matches:
        parsed = safe_json_parse(match)
        if parsed and isinstance(parsed, dict):
            return parsed
    
    return {}

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    return re.sub(r'[^\w\-_.]', '_', filename)

def format_answer(answer: Any) -> Any:
    """Format answer based on type"""
    if isinstance(answer, (int, float)):
        return answer
    elif isinstance(answer, str):
        # Try to convert string numbers
        try:
            return int(answer)
        except:
            try:
                return float(answer)
            except:
                return answer
    else:
        return str(answer)