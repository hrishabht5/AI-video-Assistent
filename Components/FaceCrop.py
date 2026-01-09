import cv2
import numpy as np
from moviepy.editor import *
from Components.Speaker import detect_faces_and_speakers, Frames
global Fps

def crop_to_vertical(input_video_path, output_video_path):
    """Crop video to vertical 9:16 format with active face tracking and smoothing"""
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    vertical_height = int(original_height)
    vertical_width = int(vertical_height * 9 / 16)
    
    # Ensure vertical_width is even
    if vertical_width % 2 != 0:
        vertical_width -= 1

    print(f"Tracking & Cropping: {original_width}x{original_height} -> {vertical_width}x{vertical_height} vertical")

    # Define output writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (vertical_width, vertical_height))
    
    global Fps
    Fps = fps

    # Tracking variables
    current_center_x = original_width // 2
    target_center_x = original_width // 2
    smoothing_factor = 0.1  # Adjust for faster/slower camera movement
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Every 3 frames, look for a face (speeds up processing)
        if frame_count % 3 == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Downscale for faster detection
            small_gray = cv2.resize(gray, (0, 0), fx=0.5, fy=0.5)
            faces = face_cascade.detectMultiScale(small_gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            if len(faces) > 0:
                # Find the best face (largest one)
                best_face = max(faces, key=lambda f: f[2] * f[3])
                # Scale face center back to original size
                face_x = (best_face[0] + best_face[2] // 2) * 2
                target_center_x = face_x
        
        # Smoothly move current_center_x towards target_center_x
        current_center_x = int(current_center_x + (target_center_x - current_center_x) * smoothing_factor)
        
        # Calculate crop bounds and clamp to video edges
        x_start = max(0, min(current_center_x - vertical_width // 2, original_width - vertical_width))
        x_end = x_start + vertical_width
        
        # Perform the crop
        cropped_frame = frame[0:vertical_height, x_start:x_end]
        
        # Handle edge cases where frame might be 1px off due to rounding
        if cropped_frame.shape[1] != vertical_width:
             cropped_frame = cv2.resize(cropped_frame, (vertical_width, vertical_height))

        out.write(cropped_frame)
        frame_count += 1
        
        if frame_count % 100 == 0:
            print(f"Processed {frame_count}/{total_frames} frames (Tracking at x={current_center_x})")

    cap.release()
    out.release()
    print(f"✓ Dynamic cropping complete for {output_video_path}")

    cap.release()
    out.release()
    print(f"Cropping complete. Processed {frame_count} frames -> {output_video_path}")



def combine_videos(video_with_audio, video_without_audio, output_filename):
    try:
        # Load video clips
        clip_with_audio = VideoFileClip(video_with_audio)
        clip_without_audio = VideoFileClip(video_without_audio)

        audio = clip_with_audio.audio

        combined_clip = clip_without_audio.set_audio(audio)

        global Fps
        print(f"Rendering final video at {Fps} FPS...")
        
        try:
            print("Attempting hardware acceleration (NVENC)...")
            combined_clip.write_videofile(
                output_filename, 
                codec='h264_nvenc', 
                audio_codec='aac', 
                fps=Fps,
                logger=None
            )
        except Exception as nv_err:
            print(f"NVENC failed ({nv_err}), falling back to CPU (libx264 ultrafast)...")
            combined_clip.write_videofile(
                output_filename, 
                codec='libx264', 
                audio_codec='aac', 
                fps=Fps,
                preset='ultrafast',
                logger=None
            )
        
        if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
            print(f"Combined video saved successfully as {output_filename}")
            return True
        else:
            print("Error: Output file was not created or is empty.")
            return False
    
    except Exception as e:
        print(f"Error combining video and audio: {str(e)}")
        return False



if __name__ == "__main__":
    input_video_path = r'Out.mp4'
    output_video_path = 'Croped_output_video.mp4'
    final_video_path = 'final_video_with_audio.mp4'
    detect_faces_and_speakers(input_video_path, "DecOut.mp4")
    crop_to_vertical(input_video_path, output_video_path)
    combine_videos(input_video_path, output_video_path, final_video_path)



