import cloudinary
import cloudinary.uploader
import requests
import os

def upload_video(file_path, cloud_name, api_key, api_secret):
    """
    Uploads a video to Cloudinary and returns the secure MP4 URL.
    """
    try:
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )

        print(f"Uploading {file_path} to Cloudinary...")
        # Upload large files in chunks (resource_type is 'video')
        response = cloudinary.uploader.upload(
            file_path, 
            resource_type="video",
            folder="ai_shorts_generator" # Optional: organize in a folder
        )

        # Get the secure URL
        secure_url = response.get("secure_url")
        print(f"✓ Upload successful! URL: {secure_url}")
        return secure_url

    except Exception as e:
        print(f"✗ Upload failed: {str(e)}")
        return None

def trigger_webhook(webhook_url, video_url, extra_data=None):
    """
    Sends the video URL to Pabbly Connect via Webhook.
    """
    if not webhook_url:
        print("Warning: No Webhook URL provided. Skipping Pabbly trigger.")
        return False

    payload = {
        "video_url": video_url,
        "type": "video/mp4"
    }
    
    # Add any extra data (like title, etc.)
    if extra_data:
        payload.update(extra_data)

    try:
        print(f"Triggering Webhook: {webhook_url}")
        response = requests.post(webhook_url, json=payload)
        
        if response.status_code == 200:
            print("✓ Webhook triggered successfully!")
            return True
        else:
            print(f"✗ Webhook failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error triggering webhook: {str(e)}")
        return False
