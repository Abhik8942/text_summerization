import yt_dlp
import whisper
from transformers import pipeline
import os
import warnings
from concurrent.futures import ThreadPoolExecutor
warnings.filterwarnings("ignore", category=UserWarning, message=".FP16 is not supported.")

whisper_model = whisper.load_model("base")

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
def download_audio_from_youtube(url, output_path="downloaded_audio"):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f"{output_path}.%(ext)s",
        'ffmpeg_location': 'C:\ffmpeg\ffmpeg.exe',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    absolute_audio_path = os.path.abspath(f"{output_path}.mp3")
    if not os.path.exists(absolute_audio_path):
        raise FileNotFoundError(f"The audio file was not found: {absolute_audio_path}")
    return absolute_audio_path
def transcribe_audio(audio_path):
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"The audio file was not found: {audio_path}")
    
    result = whisper_model.transcribe(audio_path)
    transcription = result['text'].strip()
    if not transcription:
        raise ValueError("Transcription returned an empty result.")
    return transcription

def summarize_chunk(chunk, summarizer):
    return summarizer(chunk, max_length=150, min_length=1, do_sample=False)[0]['summary_text']
def transcribe_and_summarize(url):
    try:
        audio_path = download_audio_from_youtube(url)
        transcription = transcribe_audio(audio_path)
        if not transcription:
            return "Transcription is empty; no summarization performed."
        
        max_chunk_length = 1024  
        chunks = [transcription[i:i + max_chunk_length] for i in range(0, len(transcription), max_chunk_length)]
        with ThreadPoolExecutor() as executor:
            summaries = list(executor.map(lambda chunk: summarize_chunk(chunk, summarizer), chunks))
        
        final_summary = " ".join(summaries)
        
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return final_summary or "No summary generated."
    except Exception as e:
        return f"Error during processing: {str(e)}"