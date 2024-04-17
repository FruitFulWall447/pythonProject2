from youtube_search import YoutubeSearch
from pytube import YouTube
import tempfile
import os
import moviepy.editor as mp
import youtube_dl
from PIL import Image
from io import BytesIO
import requests


def extract_audio_bytes(query):
    try:
        # Search YouTube for videos based on the query
        search_results = YoutubeSearch(query, max_results=1).to_dict()
        if search_results:
            # Get the first video ID if available
            first_result = search_results[0]
            video_id = first_result.get('id', '')

            if video_id:
                # Construct the video link
                video_link = f'https://www.youtube.com/watch?v={video_id}'
                try:
                    with youtube_dl.YoutubeDL({}) as ydl:
                        video_info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
                    print(video_info.get('categories'))
                except Exception as e:
                    print(e)
                # Get video stream
                yt = YouTube(video_link)
                # Download the video
                temp_path = tempfile.gettempdir()
                yt.streams.filter(only_audio=True).first().download(output_path=temp_path)

                # Get the downloaded audio file path
                audio_path = os.path.join(temp_path, yt.title + '.mp4')

                # Convert the downloaded video to audio (MP3)
                audio_clip = mp.AudioFileClip(audio_path)
                audio_clip.write_audiofile(audio_path.replace('.mp4', '.mp3'))

                # Read the audio file bytes
                with open(audio_path.replace('.mp4', '.mp3'), 'rb') as audio_file:
                    audio_bytes = audio_file.read()

                # Get video title and thumbnail bytes
                video_title = yt.title
                thumbnail_bytes = get_thumbnail_bytes(yt.thumbnail_url)
                video_duration = yt.length
                duration_min_sec = f"{video_duration // 60}:{video_duration % 60:02}"

                # Clean up temporary files
                os.remove(audio_path)
                os.remove(audio_path.replace('.mp4', '.mp3'))

                print("Audio bytes extracted successfully!")
                return audio_bytes, video_title, thumbnail_bytes, duration_min_sec
            else:
                print("No video ID found for the search query.")
        else:
            print("No videos found for the given query.")
    except Exception as e:
        print(f"An error occurred: {e}")


def get_thumbnail_bytes(thumbnail_url):
    response = requests.get(thumbnail_url)
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content))
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    else:
        return None