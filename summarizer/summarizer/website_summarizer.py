import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from transformers import pipeline
import torch
from concurrent.futures import ThreadPoolExecutor
import re

def clean_text(text):
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    
    # Remove special characters
    text = re.sub(r'[^\w\s.]', '', text)
    
    return text

def extract_main_content(soup):
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe', 'img']):
        element.decompose()
    
    # Try different content extraction methods
    content_candidates = [
        soup.find('article'),
        soup.find('main'),
        soup.find(class_=re.compile('content|article|body', re.IGNORECASE)),
        soup.find(id=re.compile('content|article|body', re.IGNORECASE))
    ]
    
    for candidate in content_candidates:
        if candidate:
            text = candidate.get_text(separator=' ', strip=True)
            if len(text) > 100:
                return text
    
    # Fallback to full body text
    return soup.get_text(separator=' ', strip=True)

def summarize_chunk(chunk, summarizer):
    try:
        return summarizer(chunk, max_length=150, min_length=1, do_sample=False)[0]['summary_text']
    except Exception as e:
        return f"Error summarizing chunk: {e}"

def summarize_text(text):
    if not text:
        return "Text is empty; no summarization performed."
    
    try:
        # Check if CUDA is available
        device = 0 if torch.cuda.is_available() else -1
        
        # Load the summarization pipeline
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=device)
        
        # Split the text into chunks
        max_chunk_length = 1024
        chunks = [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor() as executor:
            summaries = list(executor.map(
                lambda chunk: summarize_chunk(chunk, summarizer),
                chunks
            ))
        
        final_summary = " ".join(summaries)
        return final_summary
        
    except Exception as e:
        return f"Summarization error: {e}"

def summarize_website(url):
    try:
        # URL validation
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            raise ValueError("Invalid URL format")
        
        # Fetch website content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract and clean main content
        text_content = extract_main_content(soup)
        text_content = clean_text(text_content)
        
        if len(text_content) < 100:
            raise ValueError("Insufficient textual content for summarization")
        
        # Summarize the extracted content
        summary = summarize_text(text_content)
        return summary
    
    except requests.RequestException as req_error:
        return f"Network error: {req_error}"
    
    except Exception as general_error:
        return f"Summarization failed: {general_error}"