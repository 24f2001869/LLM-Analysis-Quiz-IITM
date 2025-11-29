from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
import uvicorn
import json
import gc
from app.auth import auth_service
from app.browser.browser_service import browser_service
from app.llm.llm_service import llm_service
from app.solvers.quiz_solver import quiz_solver
from app.config import config

from fastapi import FastAPI
import psutil
import os

app = FastAPI(title="LLM Quiz Solver", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class QuizRequest(BaseModel):
    email: str
    secret: str
    url: str

class PromptTestRequest(BaseModel):
    system_prompt: str
    user_prompt: str
    code_word: str

# Browser service status
browser_available = False


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    process = psutil.Process(os.getpid())
    return {
        "status": "healthy",
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "browser_available": browser_available
    }

@app.get("/patterns")
async def list_patterns():
    """List available quiz patterns"""
    return {
        "patterns": [
            "UV HTTP GET commands",
            "Git operations", 
            "Markdown linking",
            "Audio transcription",
            "Image color analysis",
            "CSV data processing",
            "GitHub API integration",
            "PDF invoice processing",
            "Chart type selection",
            "GitHub Actions cache"
        ]
    }

# Startup event - WITH ERROR HANDLING
@app.on_event("startup")
async def startup_event():
    global browser_available
    try:
        await browser_service.start()
        browser_available = True
        print("✅ Browser service started successfully")
    except Exception as e:
        browser_available = False
        print(f"⚠️ Browser service unavailable: {str(e)}")
        print("🔄 Using fallback mode - API will work without browser automation")

# Shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    if browser_available:
        await browser_service.close()

# Health check
@app.get("/")
async def root():
    return {
        "status": "active", 
        "service": "LLM Quiz Solver",
        "browser_available": browser_available,
        "message": "API is running" + (" with browser support" if browser_available else " in fallback mode")
    }

# Prompt testing endpoint
@app.post("/test-prompts")
async def test_prompts(request: PromptTestRequest):
    """Test prompt resistance and effectiveness"""
    try:
        resistance_result = await llm_service.test_prompt_resistance(
            request.system_prompt, request.user_prompt, request.code_word
        )
        effectiveness_result = await llm_service.test_prompt_effectiveness(
            request.system_prompt, request.user_prompt, request.code_word
        )
        
        return {
            "system_prompt_resistance": resistance_result,
            "user_prompt_effectiveness": effectiveness_result,
            "code_word": request.code_word,
            "browser_available": browser_available
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prompt testing error: {str(e)}")

# Main quiz solving endpoint
@app.post("/solve-quiz")
async def solve_quiz(request: QuizRequest):
    """Main endpoint for solving quizzes"""
    
    # Verify authentication
    auth_service.verify_secret(request.email, request.secret)
    
    try:
        # Solve the quiz
        result = await quiz_solver.solve_quiz(request.url)
        
        return {
            "status": "success",
            "original_url": request.url,
            "result": result,
            "browser_available": browser_available
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Return error but don't crash
        return {
            "status": "error",
            "error": str(e),
            "browser_available": browser_available,
            "message": "Quiz solving failed but API is responsive"
        }

# Test endpoint for demo
@app.post("/demo")
async def demo_endpoint(request: QuizRequest):
    """Demo endpoint for testing"""
    auth_service.verify_secret(request.email, request.secret)
    
    return {
        "status": "success",
        "message": "Demo endpoint working",
        "email": request.email,
        "url": request.url,
        "browser_available": browser_available
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


