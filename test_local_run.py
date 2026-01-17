import requests
import time

# API Endpoint
url = "http://127.0.0.1:8000/process"
data = {
    "url": "https://youtu.be/U6MIV_0fmc4?si=gUe6GRF3qrs8CO74",
    "auto_approve": True
}

print("🚀 Sending request to local API...")
try:
    response = requests.post(url, json=data)
    if response.status_code == 200:
        result = response.json()
        job_id = result.get("job_id")
        print(f"✅ Job started! Job ID: {job_id}")
        
        # Poll for status
        status_url = f"http://127.0.0.1:8000/status/{job_id}"
        print("⏳ Waiting for processing (Polling every 10s)...")
        
        while True:
            status_res = requests.get(status_url)
            status_data = status_res.json()
            status = status_data.get("status")
            
            print(f"Current Status: {status}")
            
            if status == "completed":
                print("🎉 SUCCESS! Video processed.")
                print("Files generated:", status_data.get("files"))
                break
            elif status == "failed":
                print("❌ FAILED!")
                print("Error:", status_data.get("error"))
                break
                
            time.sleep(10)
    else:
        print(f"❌ Server error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("Make sure your API is running (python -m uvicorn api:app --reload)")
