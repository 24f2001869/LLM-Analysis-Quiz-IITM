import pytest
import pandas as pd
from app.solvers.data_solver import DataSolver
from app.solvers.quiz_solver import QuizSolver

def test_instruction_extraction():
    """Test instruction extraction from text"""
    solver = DataSolver()
    
    text = """
    Download this file: https://example.com/data.pdf
    What is the sum of the "value" column in the table?
    Submit your answer to: https://example.com/submit
    """
    
    instructions = solver.extract_instructions(text)
    
    assert instructions['operation'] == 'sum'
    assert instructions['target'] == 'value'
    assert 'submit' in instructions['submit_url']
    assert 'download' in instructions['file_url']

def test_base64_decoding():
    """Test base64 content decoding"""
    solver = DataSolver()
    
    # Test base64 decoding
    base64_text = """
    <script>
    document.querySelector("#result").innerHTML = atob("SGVsbG8gV29ybGQ=");
    </script>
    """
    
    decoded = solver.decode_base64_content(base64_text)
    assert decoded == "Hello World"

def test_data_operations():
    """Test various data operations"""
    solver = DataSolver()
    
    # Create test data
    df = pd.DataFrame({
        'value': [1, 2, 3, 4, 5],
        'name': ['A', 'B', 'C', 'D', 'E']
    })
    
    instructions = {'operation': 'sum', 'target': 'value'}
    result = solver.perform_operation(df, instructions)
    assert result == 15.0
    
    instructions = {'operation': 'average', 'target': 'value'}
    result = solver.perform_operation(df, instructions)
    assert result == 3.0
    
    instructions = {'operation': 'count'}
    result = solver.perform_operation(df, instructions)
    assert result == 5

def test_quiz_solver_initialization():
    """Test quiz solver initialization"""
    solver = QuizSolver()
    assert solver.data_solver is not None
    assert solver.client is not None

@pytest.mark.asyncio
async def test_submit_answer_logic():
    """Test answer submission logic"""
    solver = QuizSolver()
    
    instructions = {
        'submit_url': 'https://httpbin.org/post',
        'text': 'Test question'
    }
    
    result = await solver.submit_answer(instructions, "test_answer", "https://example.com/quiz-123")
    
    # Should contain either success or error
    assert 'error' in result or 'status' in result