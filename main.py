from Components.YoutubeDownloader import download_youtube_video
from Components.Edit import extractAudio, crop_video
from Components.Transcription import transcribeAudio
from Components.LanguageTasks import GetHighlight
from Components.FaceCrop import crop_to_vertical, combine_videos
from Components.Subtitles import add_subtitles_to_video
import sys
import os
import uuid
import re

# Clean and slugify title for filename
def clean_filename(title):
    # Convert to lowercase
    cleaned = title.lower()
    # Remove or replace invalid filename characters
    cleaned = re.sub(r'[<>:"/\\|?*\[\]]', '', cleaned)
    # Replace spaces and underscores with hyphens
    cleaned = re.sub(r'[\s_]+', '-', cleaned)
    # Remove multiple consecutive hyphens
    cleaned = re.sub(r'-+', '-', cleaned)
    # Remove leading/trailing hyphens
    cleaned = cleaned.strip('-')
    # Limit length
    return cleaned[:80]

def process_video(url_or_file, auto_approve=False):
    # Generate unique session ID for this run (for concurrent execution support)
    session_id = str(uuid.uuid4())[:8]
    print(f"Session ID: {session_id}")
    
    # Check if input is a local file
    video_title = None
    if os.path.isfile(url_or_file):
        print(f"Using local video file: {url_or_file}")
        Vid = url_or_file
        # Extract title from filename
        video_title = os.path.splitext(os.path.basename(url_or_file))[0]
    else:
        # Assume it's a YouTube URL
        print(f"Downloading from YouTube: {url_or_file}")
        Vid = download_youtube_video(url_or_file)
        if Vid:
            Vid = Vid.replace(".webm", ".mp4")
            print(f"Downloaded video and audio files successfully! at {Vid}")
            # Extract title from downloaded file path
            video_title = os.path.splitext(os.path.basename(Vid))[0]

    # Process video (works for both local files and downloaded videos)
    if Vid:
        # Create unique temporary filenames
        audio_file = f"audio_{session_id}.wav"
        
        Audio = extractAudio(Vid, audio_file)
        if Audio:
            transcriptions = transcribeAudio(Audio)
            if len(transcriptions) > 0:
                print(f"\n{'='*60}")
                print(f"TRANSCRIPTION SUMMARY: {len(transcriptions)} segments")
                print(f"{'='*60}\n")
                TransText = ""

                for text, start, end in transcriptions:
                    TransText += (f"{start} - {end}: {text}\n")

                print("Analyzing transcription to find best highlights...")
                highlights = GetHighlight(TransText)
                
                # Check if GetHighlight failed
                if not highlights:
                    print(f"\n{'='*60}")
                    print("ERROR: Failed to get highlights from AI")
                    print(f"{'='*60}")
                    print(f"\nTranscription summary:")
                    print(f"  Total segments: {len(transcriptions)}")
                    print(f"  Total length: {len(TransText)} characters")
                    print(f"{'='*60}\n")
                    return []
                
                output_files = []
                print(f"\n✓ Found {len(highlights)} segments to process.")

                for i, highlight in enumerate(highlights):
                    if not isinstance(highlight, dict):
                        print(f"Skipping invalid highlight {i+1}")
                        continue
                        
                    start = highlight.get('start')
                    stop = highlight.get('end')
                    
                    if start is None or stop is None:
                        print(f"Skipping highlight {i+1} due to missing start/end")
                        continue
                    
                    #handle the case when the highlight starts from 0s
                    if not (start>=0 and stop>0 and stop>start):
                        print(f"Skipping highlight {i+1} due to invalid time range: {start}s - {stop}s")
                        continue

                    print(f"\n{'='*60}")
                    print(f"PROCESSING HIGHLIGHT {i+1}/{len(highlights)}")
                    print(f"Time: {start}s - {stop}s ({stop-start}s duration)")
                    print(f"{'='*60}\n")

                    # Create unique temporary filenames for this segment
                    temp_clip = f"temp_clip_{session_id}_{i}.mp4"
                    temp_cropped = f"temp_cropped_{session_id}_{i}.mp4"

                    print(f"Step 1/3 (Part {i+1}): Extracting clip from original video...")
                    crop_video(Vid, temp_clip, start, stop)

                    print(f"Step 2/3 (Part {i+1}): Cropping to vertical format (9:16) with Active Tracking...")
                    crop_to_vertical(temp_clip, temp_cropped)
                    
                    # Generate final output filename
                    clean_title = clean_filename(video_title) if video_title else "output"
                    final_output = f"{clean_title}_part{i+1}_{session_id}_short.mp4"
                    
                    print(f"Step 3/3 (Part {i+1}): Adding audio to final video...")
                    success = combine_videos(temp_clip, temp_cropped, final_output)
                    
                    if success:
                        print(f"\n✓ SUCCESS: Highlight {i+1} saved as {final_output}")
                        output_files.append(final_output)
                    else:
                        print(f"\n✗ FAILED: Could not create Highlight {i+1}")
                    
                    # Clean up temporary files for this segment
                    try:
                        for f in [temp_clip, temp_cropped]:
                            if os.path.exists(f):
                                os.remove(f)
                    except Exception as e:
                        print(f"Warning: Cleanup failed for part {i+1}: {e}")

                print(f"\n{'='*60}")
                print(f"✓ ALL DONE: Processed {len(highlights)} highlights.")
                print(f"{'='*60}\n")
                
                # Final cleanup
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                
                return output_files
            else:
                print("No transcriptions found")
                return []
        else:
            print("No audio file found")
            return []
    else:
        print("Unable to process the video")
        return []

if __name__ == "__main__":
    # Check for auto-approve flag (for batch processing)
    auto_approve = "--auto-approve" in sys.argv
    if auto_approve:
        sys.argv.remove("--auto-approve")

    # Check if URL/file was provided as command-line argument
    if len(sys.argv) > 1:
        url_or_file = sys.argv[1]
        print(f"Using input from command line: {url_or_file}")
    else:
        url_or_file = input("Enter YouTube video URL or local video file path: ")

    process_video(url_or_file, auto_approve=auto_approve)
