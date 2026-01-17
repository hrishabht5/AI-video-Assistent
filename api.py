from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import uuid
import shutil
from main import process_video

app = FastAPI(title="AI Video Assistant API")

# Store job status
jobs = {}

class VideoRequest(BaseModel):
    url: str
    auto_approve: bool = True

@app.get("/")
def read_root():
    return {"message": "AI Video Assistant API is running"}

@app.post("/process")
def start_processing(request: VideoRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "processing", "files": []}
    
    background_tasks.add_task(run_processing, job_id, request.url, request.auto_approve)
    
    return {"job_id": job_id, "status": "started"}

@app.get("/status/{job_id}")
def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = filename # Files are saved in the root or 'videos' depending on main.py
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

def run_processing(job_id: str, url: str, auto_approve: bool):
    # Cloudinary Config
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
    PABBLY_WEBHOOK_URL = os.getenv("PABBLY_WEBHOOK_URL")

    cloudinary_config = None
    if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
        cloudinary_config = {
            "cloud_name": CLOUDINARY_CLOUD_NAME,
            "api_key": CLOUDINARY_API_KEY,
            "api_secret": CLOUDINARY_API_SECRET
        }

    try:
        output_files = process_video(url, auto_approve=auto_approve, cloudinary_config=cloudinary_config, webhook_url=PABBLY_WEBHOOK_URL)
        jobs[job_id] = {"status": "completed", "files": output_files}
    except Exception as e:
        jobs[job_id] = {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
