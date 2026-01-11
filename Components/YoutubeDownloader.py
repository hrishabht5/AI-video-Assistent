import os
import re
from pytubefix import YouTube
import ffmpeg

def get_video_size(stream):

    return stream.filesize / (1024 * 1024)

def download_youtube_video(url):
    try:
        # Using standard YouTube call to avoid interactive OAuth prompts in headless API environments
        yt = YouTube(url)

        video_streams = yt.streams.filter(type="video").order_by('resolution').desc()
        audio_stream = yt.streams.filter(only_audio=True).first()

        # Show available streams
        print("\nAvailable video streams:")
        top_streams = video_streams[:8]  # Show more options to find 1080p
        for i, stream in enumerate(top_streams):
            size = get_video_size(stream)
            stream_type = "Progressive" if stream.is_progressive else "Adaptive"
            print(f"  {i}. Resolution: {stream.resolution}, Size: {size:.2f} MB, Type: {stream_type}")
        
        # Interactive selection with timeout
        import select
        import sys
        
        # Try to find 1080p stream index for auto-select
        auto_index = 0
        for i, s in enumerate(top_streams):
            if s.resolution == '1080p':
                auto_index = i
                break

        print(f"\nSelect resolution number (0-{len(top_streams)-1}) or wait 5s for auto-select...")
        print(f"Auto-selecting {top_streams[auto_index].resolution} quality in 5 seconds...")
        
        selected_stream = None
        try:
            ready, _, _ = select.select([sys.stdin], [], [], 5)
            if ready:
                user_input = sys.stdin.readline().strip()
                if user_input.isdigit():
                    choice = int(user_input)
                    if 0 <= choice < len(top_streams):
                        selected_stream = top_streams[choice]
                        print(f"✓ User selected: {selected_stream.resolution}")
                    else:
                        print(f"Invalid choice, using {top_streams[auto_index].resolution} quality")
                        selected_stream = top_streams[auto_index]
                else:
                    print(f"Invalid input, using {top_streams[auto_index].resolution} quality")
                    selected_stream = top_streams[auto_index]
            else:
                print(f"\nTimeout - auto-selecting {top_streams[auto_index].resolution} quality")
                selected_stream = top_streams[auto_index]
        except:
            print(f"\nAuto-selecting {top_streams[auto_index].resolution} quality (timeout not available on this platform)")
            selected_stream = top_streams[auto_index]
        
        # Confirm selection
        if selected_stream is None:
            selected_stream = top_streams[auto_index]
        
        size = get_video_size(selected_stream)
        stream_type = "Progressive" if selected_stream.is_progressive else "Adaptive"
        print(f"\nFinal selection: {selected_stream.resolution}, Size: {size:.2f} MB, Type: {stream_type}")

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

if __name__ == "__main__":
    youtube_url = input("Enter YouTube video URL: ")
    download_youtube_video(youtube_url)
