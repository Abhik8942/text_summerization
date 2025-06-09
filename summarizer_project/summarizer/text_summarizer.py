from transformers import pipeline
from concurrent.futures import ThreadPoolExecutor
import torch
# Function to summarize a chunk of text
def summarize_chunk(chunk, summarizer):
    return summarizer(chunk, max_length=150, min_length=1, do_sample=False)[0]['summary_text']
# Function to summarize the entire text
def summarize_text(text):
    # Check if CUDA is available
    device = 0 if torch.cuda.is_available() else -1
    # Load the summarization pipeline
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=device)
    if not text:
        return "Text is empty; no summarization performed."
    # Split the text into chunks
    max_chunk_length = 1024  
    chunks = [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor() as executor:
        summaries = list(executor.map(lambda chunk: summarize_chunk(chunk, summarizer), chunks))
    final_summary = " ".join(summaries)
    return final_summary