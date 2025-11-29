import pandas as pd
import numpy as np
import requests
import pdfplumber
import json
from io import BytesIO
from .base_solver import BaseSolver

class DataSolver(BaseSolver):
    async def solve(self, instructions: str, data: any) -> any:
        """Solve data-related quiz questions"""
        
        parsed_instructions = self.extract_instructions(instructions)
        
        # Download and process file if needed
        if parsed_instructions.get('file_url'):
            file_data = await self.download_file(parsed_instructions['file_url'])
            processed_data = await self.process_file(file_data, parsed_instructions)
            result = await self.perform_operation(processed_data, parsed_instructions)
        else:
            result = await self.perform_operation(data, parsed_instructions)
        
        return result
    
    async def download_file(self, url: str) -> bytes:
        """Download file from URL"""
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    
    async def process_file(self, file_data: bytes, instructions: dict) -> any:
        """Process different file types"""
        
        # Try CSV first (most common)
        try:
            df = pd.read_csv(BytesIO(file_data))
            return df
        except:
            pass
        
        # Try JSON
        try:
            json_data = json.loads(file_data.decode('utf-8'))
            # Convert JSON to DataFrame if it's a list
            if isinstance(json_data, list):
                return pd.DataFrame(json_data)
            return json_data
        except:
            pass
        
        # Try PDF
        try:
            with pdfplumber.open(BytesIO(file_data)) as pdf:
                text = ""
                tables = []
                
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
                
                if tables:
                    # Convert tables to DataFrame
                    dfs = []
                    for table in tables:
                        if table and len(table) > 1:  # Has header and data
                            df_table = pd.DataFrame(table[1:], columns=table[0])
                            dfs.append(df_table)
                    
                    if dfs:
                        # Return first table or concatenate
                        return dfs[0] if len(dfs) == 1 else pd.concat(dfs, ignore_index=True)
                
                # Return text data
                return pd.DataFrame({'text': [text]})
        except:
            pass
        
        # Try ZIP file (for logs)
        try:
            import zipfile
            with zipfile.ZipFile(BytesIO(file_data)) as zip_file:
                # Process each file in zip
                for file_name in zip_file.namelist():
                    if file_name.endswith('.json') or file_name.endswith('.jsonl'):
                        with zip_file.open(file_name) as f:
                            content = f.read().decode('utf-8')
                            # Parse JSON lines
                            lines = content.strip().split('\n')
                            data = [json.loads(line) for line in lines if line.strip()]
                            return pd.DataFrame(data)
        except:
            pass
        
        # Return as text as last resort
        return pd.DataFrame({'content': [file_data.decode('utf-8', errors='ignore')]})
    
    async def perform_operation(self, data: any, instructions: dict) -> any:
        """Perform data operation based on instructions"""
        
        # Handle DataFrame operations
        if isinstance(data, pd.DataFrame):
            operation = instructions.get('operation', '').lower()
            target = instructions.get('target')
            
            if operation == 'sum' and target:
                if target in data.columns:
                    return float(data[target].sum())
            elif operation == 'average' and target:
                if target in data.columns:
                    return float(data[target].mean())
            elif operation == 'count':
                return len(data)
            elif operation == 'max' and target:
                if target in data.columns:
                    return float(data[target].max())
            elif operation == 'min' and target:
                if target in data.columns:
                    return float(data[target].min())
            
            # Special: Running totals by group (for orders CSV)
            if 'running totals' in str(instructions).lower() and 'customer_id' in str(instructions):
                if 'customer_id' in data.columns and 'amount' in data.columns:
                    # Sort by date first
                    if 'order_date' in data.columns:
                        data = data.sort_values('order_date')
                    
                    # Calculate running totals by customer
                    data['running_total'] = data.groupby('customer_id')['amount'].cumsum()
                    
                    # Get final totals and top 3
                    final_totals = data.groupby('customer_id')['running_total'].last().sort_values(ascending=False)
                    top_3 = final_totals.head(3)
                    
                    # Format as required JSON
                    result = [{"customer_id": cust, "total": float(total)} 
                             for cust, total in top_3.items()]
                    return json.dumps(result)
            
            # Default: return first numeric value
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            if len(numeric_columns) > 0:
                return float(data[numeric_columns[0]].iloc[0])
        
        # Handle JSON data directly
        elif isinstance(data, (list, dict)):
            # For logs analysis: sum bytes where event=="download"
            if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                if any('event' in item and 'bytes' in item for item in data):
                    download_sum = sum(item['bytes'] for item in data 
                                     if item.get('event') == 'download')
                    return download_sum
        
        return "Unable to compute answer"
    
    def decode_base64_content(self, base64_content: str) -> str:
        """Decode base64 encoded content from quiz pages"""
        if not base64_content:
            return ""
        
        try:
            import base64
            # Extract base64 string from JavaScript
            base64_match = re.search(r'atob\(["\']([^"\']+)["\']\)', base64_content)
            if base64_match:
                encoded_str = base64_match.group(1)
                decoded_bytes = base64.b64decode(encoded_str)
                return decoded_bytes.decode('utf-8')
        except:
            pass
        
        return ""
    
    def extract_instructions(self, instructions_text: str) -> dict:
        """Extract structured instructions from text"""
        parsed = {}
        text_lower = instructions_text.lower()
        
        # Extract file URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, instructions_text)
        if urls:
            for url in urls:
                if any(keyword in url.lower() for keyword in ['download', 'file', 'csv', 'pdf', 'json', 'zip']):
                    parsed['file_url'] = url
                    break
        
        # Extract operations
        if 'sum' in text_lower:
            parsed['operation'] = 'sum'
        elif 'average' in text_lower or 'mean' in text_lower:
            parsed['operation'] = 'average'
        elif 'count' in text_lower:
            parsed['operation'] = 'count'
        elif 'max' in text_lower or 'maximum' in text_lower:
            parsed['operation'] = 'max'
        elif 'min' in text_lower or 'minimum' in text_lower:
            parsed['operation'] = 'min'
        
        # Extract target columns
        col_match = re.search(r'["\']([^"\']+)["\'] column', instructions_text, re.IGNORECASE)
        if col_match:
            parsed['target'] = col_match.group(1)
        
        return parsed
