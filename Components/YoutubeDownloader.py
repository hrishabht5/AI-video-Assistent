import os
import re
from pytubefix import YouTube
import ffmpeg

def get_video_size(stream):

    return stream.filesize / (1024 * 1024)

def download_youtube_video(url):
    try:
        # Using 'TV' client - Currently the MOST robust way to bypass 403 Forbidden on Cloud/Colab IPs.
        # It will prompt for OAuth login at google.com/device.
        yt = YouTube(url, client='TV', use_oauth=True, allow_oauth_cache=True)

        # Auto-select the best available video stream (up to 1080p for stability)
        video_streams = yt.streams.filter(type="video").order_by('resolution').desc()
        
        selected_stream = None
        # Try to find 1080p, else take the top one
        for s in video_streams[:5]:
            if s.resolution == '1080p':
                selected_stream = s
                break
        
        if not selected_stream:
            selected_stream = video_streams.first()

        audio_stream = yt.streams.filter(only_audio=True).first()
        
        size = get_video_size(selected_stream)
        stream_type = "Progressive" if selected_stream.is_progressive else "Adaptive"
        print(f"Auto-selected quality: {selected_stream.resolution}, Size: {size:.2f} MB, Type: {stream_type}")

        if not os.path.exists('videos'):
            os.makedirs('videos')

        print(f"Downloading video: {yt.title}")
        video_file = selected_stream.download(output_path='videos', filename_prefix="video_")

        if not selected_stream.is_progressive:
            print("Downloading audio...")
            audio_file = audio_stream.download(output_path='videos', filename_prefix="audio_")

            print("Merging video and audio with hardware acceleration...")
            # Sanitize title for filename to avoid "Invalid argument" errors (e.g., characters like '|')
            safe_title = re.sub(r'[<>:"/\\|?*]', '', yt.title)
            output_file = os.path.join('videos', f"{safe_title}.mp4")
            
            # Use h264_nvenc for much faster merging if possible
            try:
                stream = ffmpeg.input(video_file)
                audio = ffmpeg.input(audio_file)
                # Try NVENC first - using standard parameters for better compatibility
                stream = ffmpeg.output(stream, audio, output_file, vcodec='h264_nvenc', acodec='aac', strict='experimental')
                ffmpeg.run(stream, overwrite_output=True)
            except ffmpeg.Error:
                print("NVENC failed or not available, falling back to CPU (libx264 veryfast)")
                stream = ffmpeg.input(video_file)
                audio = ffmpeg.input(audio_file)
                stream = ffmpeg.output(stream, audio, output_file, vcodec='libx264', acodec='aac', strict='experimental', preset='veryfast')
                ffmpeg.run(stream, overwrite_output=True)

            os.remove(video_file)
            os.remove(audio_file)
        else:
            output_file = video_file

        
        print(f"Downloaded: {yt.title} to 'videos' folder")
        # Ensure we return a path with the same sanitized title used in downloading/merging
        return output_file

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please make sure you have the latest version of pytube and ffmpeg-python installed.")
        print("You can update them by running:")
        print("pip install --upgrade pytube ffmpeg-python")
        print("Also, ensure that ffmpeg is installed on your system and available in your PATH.")
        return None

if __name__ == "__main__":
    youtube_url = input("Enter YouTube video URL: ")
    download_youtube_video(youtube_url)
