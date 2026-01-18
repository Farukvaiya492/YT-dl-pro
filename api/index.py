import httpx
import urllib.parse
import re
import base64
import time
import random
import string
from fastapi import FastAPI, Query, Request
from fastapi.responses import StreamingResponse

app = FastAPI()

def generate_random_id(length=20):
    """রেন্ডম সেশন আইডি জেনারেট করার ফাংশন"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def format_duration(seconds: int):
    """সেকেন্ডকে HH:MM:SS ফরম্যাটে রূপান্তর"""
    if not seconds: return "00:00"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

def clean_filename(title: str):
    """টাইটেল থেকে ক্লিন ফাইল নেম তৈরি"""
    clean = re.sub(r'[^\w\s-]', '', title)
    return clean.strip().replace(' ', '_')

@app.get("/")
async def home():
    return {"status": "active", "dev": "@Offline_669", "endpoint": "/api?url=LINK"}

# ভিডিও ও অডিওর জন্য প্রক্সি (ডোমেইন হাইড থাকবে)
@app.get("/proxy-stream")
async def proxy_stream(data: str, filename: str, ext: str = "mp4"):
    real_url = base64.b64decode(data).decode()
    async def stream_generator():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", real_url, follow_redirects=True) as response:
                async for chunk in response.aiter_bytes(chunk_size=1024 * 64):
                    yield chunk
    
    media_type = "audio/mpeg" if ext == "mp3" else "video/mp4"
    return StreamingResponse(
        stream_generator(),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}.{ext}"'}
    )

@app.get("/api")
async def get_video_links(request: Request, url: str = Query(...)):
    target_api = "https://thesocialcat.com/api/youtube-download"
    base_url = str(request.base_url).rstrip("/")
    
    # কুকি ও সেশন রেন্ডমাইজ করা হচ্ছে
    timestamp = int(time.time() * 1000)
    ga_id = f"GA1.1.{random.randint(1000000000, 9999999999)}.{int(time.time())}"
    session_id = f"{timestamp}${generate_random_id(5)}$g0$t{timestamp}"
    
    # আপনার দেওয়া হেডার্স যা রেন্ডমলি আপডেট হবে
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
        'Content-Type': "application/json",
        'origin': "https://thesocialcat.com",
        'referer': "https://thesocialcat.com/tools/youtube-video-downloader",
        'accept-language': "en-US,en;q=0.9,bn;q=0.8",
        'Cookie': f"_ga={ga_id}; _fbp=fb.1.{timestamp}.{random.randint(100, 999)}; _ga_ZECYDJ3Y4Y=GS2.1.s{session_id}; dmcfkjn3cdc={generate_random_id(26).lower()}; theme=dark"
    }

    formats = ["720p", "audio"]
    results = []
    info = {}

    async with httpx.AsyncClient() as client:
        for fmt in formats:
            try:
                payload = {"url": url, "format": fmt}
                # মূল রিকোয়েস্ট পাঠানো
                resp = await client.post(target_api, json=payload, headers=headers, timeout=15)
                
                if resp.status_code == 200:
                    data = resp.json()
                    media_url = data.get('mediaUrl')
                    
                    if not info:
                        duration_raw = data.get("videoMeta", {}).get("duration", 0)
                        info = {
                            "title": data.get('caption'),
                            "duration": format_duration(duration_raw),
                            "thumbnail": data.get('thumbnail'),
                            "author": data.get('username'),
                            "dev": "API Dev @Offline_669"
                        }

                    if media_url:
                        clean_name = clean_filename(info["title"])
                        encoded_url = base64.b64encode(media_url.encode()).decode()
                        extension = "mp3" if fmt == "audio" else "mp4"
                        
                        # আপনার নিজের ডোমেইন এবং ক্লিন লিঙ্ক
                        final_link = f"{base_url}/proxy-stream?data={encoded_url}&filename={urllib.parse.quote(clean_name)}&ext={extension}"
                        
                        results.append({
                            "quality": "MP3 Audio" if fmt == "audio" else fmt,
                            "download_url": final_link,
                            "type": fmt
                        })
            except: continue

    return {
        "success": True,
        "video_info": info,
        "mediaUrl": results[0]["download_url"] if results else None,
        "mediaUrls": results
    }
