import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Header, BackgroundTasks

from app.services.ingestion import IngestionService
from app.services.rag_agent import TestGenAgent
from app.services.selenium_agent import SeleniumAgent
from app.core.config import settings
from app.core.logger import get_logger

router = APIRouter()
logger = get_logger("api_routes")

ingestion_service = IngestionService()
# selenium_agent = SeleniumAgent() 

from pydantic import BaseModel

class TestGenerationRequest(BaseModel):
    query: str
    session_id: str

class ScriptGenerationRequest(BaseModel):
    test_case: str
    session_id: str 

@router.get("/health")
async def health_check():
    return {"status": "operational", "version": "2.0"}

@router.post("/session/start")
async def start_session():
    new_id = str(uuid.uuid4())
    logger.info(f"New session started: {new_id}")
    return {"session_id": new_id}

@router.post("/ingest")
async def ingest_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    session_id: str = Header(None)
):
    if not session_id:
        raise HTTPException(status_code=400, detail="Session-ID header required")

    session_upload_dir = os.path.join(settings.UPLOAD_DIR, session_id)
    os.makedirs(session_upload_dir, exist_ok=True)
    
    saved_paths = []
    try:
        for file in files:
            file_path = os.path.join(session_upload_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_paths.append(file_path)
        
        result = ingestion_service.process_documents(session_id, saved_paths)
        
        return result
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-tests")
async def generate_tests(request: TestGenerationRequest):
    try:
        agent = TestGenAgent(session_id=request.session_id)
        result = agent.generate_tests(request.query)
        return {"result": result}
    except Exception as e:
        logger.error(f"Test Gen Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-script")
async def generate_script(request: ScriptGenerationRequest):
    """
    Phase 3: RAG-Enhanced Selenium Agent
    1. LOCATE the HTML file uploaded by THIS specific user (Session ID).
    2. Initialize the Agent with the Session ID (to access the Vector DB for rules).
    3. Generate the script using the User's HTML + User's Rules.
    """
    try:
        # 1. Define the path to this session's upload folder
        session_upload_dir = os.path.join(settings.UPLOAD_DIR, request.session_id)
        
        # 2. Find the HTML file in that folder
        html_content = None
        html_filename = "checkout.html" # Default name, or we can scan for any .html
        
        if os.path.exists(session_upload_dir):
            # Scan for any .html file in the session folder
            for file in os.listdir(session_upload_dir):
                if file.lower().endswith(".html"):
                    found_path = os.path.join(session_upload_dir, file)
                    logger.info(f"Session {request.session_id}: Found HTML target -> {file}")
                    
                    with open(found_path, "r", encoding="utf-8") as f:
                        html_content = f.read()
                    break # Stop after finding the first HTML file
        
        # 3. Error Handling: If the user never uploaded an HTML file
        if not html_content:
            msg = "No HTML file found for this session. Please go to Tab 1 and upload your target HTML file."
            logger.warning(f"Session {request.session_id}: {msg}")
            raise HTTPException(status_code=404, detail=msg)
            
        # 4. Initialize Agent (Connects to the User's Vector DB for Rules)
        agent = SeleniumAgent(session_id=request.session_id)
        
        # 5. Generate Script
        script = agent.generate_script(request.test_case, html_content)
        
        return {"script": script}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Script Gen Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))