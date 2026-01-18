import requests
import json
import base64
import random
import string
import time
import urllib.parse
import re
import os
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

# প্যাথ ফিক্সিং: প্রোজেক্টের রুট থেকে templates ফোল্ডার খুঁজে বের করা
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
templates_path = os.path.join(root_dir, "templates")

templates = Jinja2Templates(directory=templates_path)

def generate_random_id(length=20):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def format_duration(seconds: int):
    if not seconds: return "00:00"
    h, m, s = seconds // 3600, (seconds % 3600) // 60, seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

def clean_filename(title: str):
    return re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')

@app.get("/")
def read_root(request: Request):
    """এটি এখন নির্ভুলভাবে templates/index.html লোড করবে"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api")
def download_youtube(request: Request, url: str = Query(...)):
    target_api = "https://thesocialcat.com/api/youtube-download"
    base_url = str(request.base_url).rstrip("/")
    
    qualities = ["1080p", "720p", "480p", "360p", "240p", "144p", "audio"]
    all_results = []
    video_info = {}

    for q in qualities:
        timestamp = int(time.time() * 1000)
        ga_id = f"GA1.1.{random.randint(1000, 9999)}.{int(time.time())}"
        session_id = f"{timestamp}${generate_random_id(5)}$g0$t{timestamp}"
        
        headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
            'Content-Type': "application/json",
            'origin': "https://thesocialcat.com",
            'Cookie': f"_ga={ga_id}; _ga_ZECYDJ3Y4Y=GS2.1.s{session_id}; dmcfkjn3cdc={generate_random_id(26).lower()}"
        }

        try:
            payload = {"url": url, "format": q}
            response = requests.post(target_api, data=json.dumps(payload), headers=headers, timeout=8)
            if response.status_code == 200:
                data = response.json()
                media_url = data.get("mediaUrl")
                if media_url:
                    if not video_info:
                        video_info = {
                            "title": data.get("caption", "YouTube Video"),
                            "duration": format_duration(data.get("videoMeta", {}).get("duration", 0)),
                            "thumbnail": data.get("thumbnail"),
                            "author": data.get("username"),
                            "dev": "API Dev @Offline_669"
                        }
                    
                    clean_name = clean_filename(video_info["title"])
                    encoded_url = base64.b64encode(media_url.encode()).decode()
                    ext = "mp3" if q == "audio" else "mp4"
                    
                    proxy_link = f"{base_url}/file-stream?data={encoded_url}&name={urllib.parse.quote(clean_name)}&ext={ext}"
                    all_results.append({"quality": "MP3 Audio" if q == "audio" else q, "download_url": proxy_link, "type": q})
        except: continue

    return {"ok": True, "video_info": video_info, "results": all_results} if all_results else {"ok": False}

@app.get("/file-stream")
def file_stream(data: str = Query(...), name: str = Query("video"), ext: str = Query("mp4")):
    try:
        real_url = base64.b64decode(data).decode()
        
        req = requests.get(real_url, stream=True, timeout=120)
        headers = {
            "Content-Disposition": f'attachment; filename="{name}.{ext}"',
            "Content-Type": "audio/mpeg" if ext == "mp3" else "video/mp4"
        }
        return StreamingResponse(req.iter_content(chunk_size=1024*512), headers=headers)
    except: raise HTTPException(status_code=500, detail="Error")
