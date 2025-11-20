import pandas as pd
import numpy as np
import requests
import pdfplumber
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
    
    async def process_file(self, file_data: bytes, instructions: dict) -> pd.DataFrame:
        """Process different file types"""
        # Try PDF first
        try:
            with pdfplumber.open(BytesIO(file_data)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
                
                # Extract tables from PDF
                tables = []
                for page in pdf.pages:
                    tables.extend(page.extract_tables())
                
                if tables:
                    # Convert first table to DataFrame
                    df = pd.DataFrame(tables[0][1:], columns=tables[0][0])
                    return df
                else:
                    # Return text data
                    return pd.DataFrame({'text': [text]})
        except:
            pass
        
        # Try CSV
        try:
            df = pd.read_csv(BytesIO(file_data))
            return df
        except:
            pass
        
        # Return as text
        return pd.DataFrame({'content': [file_data.decode('utf-8', errors='ignore')]})
    
    async def perform_operation(self, data: pd.DataFrame, instructions: dict) -> any:
        """Perform data operation based on instructions"""
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
        
        # Default: return first numeric value
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) > 0:
            return float(data[numeric_columns[0]].iloc[0])
        
        return "Unable to compute answer"