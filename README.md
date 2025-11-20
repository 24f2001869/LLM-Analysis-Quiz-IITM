# LLM Quiz Solver - IITM Project

A FastAPI-based application that solves data analysis quizzes using LLMs and browser automation.

## Features

- **Secure Authentication**: JWT-like secret verification with rate limiting
- **Browser Automation**: Playwright for JavaScript-heavy page rendering
- **LLM Integration**: Multiple free model providers (Hugging Face, Ollama)
- **Data Processing**: PDF extraction, CSV parsing, data analysis
- **Quiz Solving**: Automatic instruction parsing and answer submission
- **Comprehensive Testing**: 50+ tests covering all edge cases

## Deployment on Render

1. **Fork this repository** to your GitHub account

2. **Create new Web Service** on Render:
   - Connect your GitHub repository
   - Set build command:
     ```bash
     pip install -r requirements.txt
     playwright install chromium
     ```
   - Set start command:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

3. **Environment Variables** (optional):
   - `HUGGINGFACE_API_URL`: For LLM integration
   - `OLLAMA_BASE_URL`: For local Ollama models

## API Endpoints

### Main Quiz Solver
```http
POST /solve-quiz
Content-Type: application/json

{
  "email": "your-email@example.com",
  "secret": "your-secret",
  "url": "https://quiz-url"
}