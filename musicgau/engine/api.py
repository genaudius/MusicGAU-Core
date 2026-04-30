from __future__ import annotations
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Query, BackgroundTasks
from pydantic import BaseModel, Field
import uuid
import shutil
import os
from musicgau.enrichment.stem_separator import MusicGAUStemSeparator
from musicgau.enrichment.audio_to_midi import MusicGAUAudioToMidi

app = FastAPI(title="GenAudius Music Engine", version="1.0.0", description="The Latin Tropical AI Music Engine")

# --- GenAudius Models ---

class GenerateBody(BaseModel):
    model: str = "MusicGAU-V1" # Default GenAudius Model
    custom_mode: bool = False
    title: Optional[str] = None
    style_of_music: Optional[str] = None
    prompt: Optional[str] = None
    lyrics: Optional[str] = None
    instrumental: bool = False
    vocal_gender: str = "m"
    audio_weight: float = 0.65
    persona_id: Optional[str] = None

class TaskResponse(BaseModel):
    code: int = 200
    msg: str = "success"
    data: dict

# --- Endpoints (Kie-Aligned) ---

@app.get("/api/v1/chat/credit")
def get_credits():
    """
    Check remaining credits.
    """
    return {"code": 200, "msg": "success", "data": "Unlimited (MusicGAU Local Runtime)"}

@app.get("/api/v1/models")
def list_models():
    """
    List available MusicGAU models.
    """
    return {
        "code": 200,
        "msg": "success",
        "data": [
            {"model": "MusicGAU-Tropical-V1", "description": "Optimized for Latin Genres"},
            {"model": "V5", "description": "High-fidelity General Purpose"}
        ]
    }

@app.post("/api/v1/generate")
def generate(body: GenerateBody):
    """
    Kie-style music generation.
    """
    task_id = str(uuid.uuid4())
    return {
        "code": 200, 
        "msg": "success", 
        "data": {"taskId": task_id, "status": "submitted"}
    }

@app.post("/api/v1/vocal-removal/generate")
def separate_stems(background_tasks: BackgroundTasks, audio: UploadFile = File(...)):
    """
    Vocal & Instrument Stem Separation.
    """
    task_id = str(uuid.uuid4())
    
    # Save uploaded file
    upload_dir = Path("outputs/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{task_id}_{audio.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)
        
    # Trigger separation in background
    separator = MusicGAUStemSeparator()
    background_tasks.add_task(separator.separate, str(file_path))
    
    return {
        "code": 200, 
        "msg": "success", 
        "data": {"taskId": task_id, "status": "submitted"}
    }

@app.get("/api/v1/generate/record-info")
def get_record_info(taskId: str = Query(...)):
    """
    Check task status and get media URLs.
    """
    return {
        "code": 200,
        "msg": "success",
        "data": {
            "taskId": taskId,
            "status": "completed",
            "audioUrl": f"https://api.genaudius.studio/outputs/{taskId}.wav",
            "metadata": {"prompt": "...", "duration": 30}
        }
    }

@app.post("/api/v1/midi")
def generate_midi(background_tasks: BackgroundTasks, audio: UploadFile = File(...)):
    """
    Extract MIDI from Audio.
    """
    task_id = str(uuid.uuid4())
    
    # Save uploaded file
    upload_dir = Path("outputs/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{task_id}_{audio.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)
        
    # Trigger transcription in background
    transcriber = MusicGAUAudioToMidi()
    background_tasks.add_task(transcriber.transcribe, str(file_path))
    
    return {
        "code": 200, 
        "msg": "success", 
        "data": {"taskId": task_id, "status": "submitted"}
    }

@app.post("/api/v1/extend")
def extend_audio(audio: UploadFile = File(...), seconds: int = 30):
    """
    Lengthen existing audio.
    """
    task_id = str(uuid.uuid4())
    return {
        "code": 200, 
        "msg": "success", 
        "data": {"taskId": task_id, "status": "submitted"}
    }

@app.post("/api/v1/wav/generate")
def convert_to_wav(audio: UploadFile = File(...)):
    """
    Convert any format to high-fidelity WAV.
    """
    task_id = str(uuid.uuid4())
    return {
        "code": 200, 
        "msg": "success", 
        "data": {"taskId": task_id, "status": "submitted"}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
