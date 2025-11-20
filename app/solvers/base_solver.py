from abc import ABC, abstractmethod
import base64
import re

class BaseSolver(ABC):
    def __init__(self):
        self.supported_operations = [
            'sum', 'count', 'average', 'max', 'min', 'filter', 'sort',
            'extract', 'download', 'analyze', 'visualize'
        ]
    
    @abstractmethod
    async def solve(self, instructions: str, data: any) -> any:
        pass
    
    def extract_instructions(self, text: str) -> dict:
        """Extract quiz instructions from text"""
        instructions = {
            'operation': None,
            'target': None,
            'submit_url': None,
            'file_url': None
        }
        
        # Find submit URL
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        for url in urls:
            if 'submit' in url.lower():
                instructions['submit_url'] = url
            elif 'download' in text.lower() and url not in instructions.values():
                instructions['file_url'] = url
        
        # Find operations
        for op in self.supported_operations:
            if op in text.lower():
                instructions['operation'] = op
                break
        
        # Find targets (like "value column", "page 2", etc.)
        if 'column' in text.lower():
            col_match = re.search(r'["\']([^"\']+)["\'] column', text, re.IGNORECASE)
            if col_match:
                instructions['target'] = col_match.group(1)
        
        return instructions
    
    def decode_base64_content(self, base64_text: str) -> str:
        """Decode base64 content from script tags"""
        try:
            # Extract base64 encoded string
            b64_match = re.search(r'atob\(["\']([^"\']+)["\']\)', base64_text)
            if b64_match:
                encoded = b64_match.group(1)
                decoded = base64.b64decode(encoded).decode('utf-8')
                return decoded
        except:
            pass
        return ""