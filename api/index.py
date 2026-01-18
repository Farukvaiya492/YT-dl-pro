import requests
import json
import base64
import random
import string
import time
import urllib.parse
import re
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import StreamingResponse

app = FastAPI()

def generate_random_id(length=20):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def format_duration(seconds: int):
    if not seconds: return "00:00"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def clean_filename(title: str):
    clean = re.sub(r'[^\w\s-]', '', title)
    return clean.strip().replace(' ', '_')

@app.get("/")
def home():
    return {"status": "active", "dev": "@Offline_669"}

@app.get("/api")
def download_youtube(request: Request, url: str = Query(...)):
    target_api = "https://thesocialcat.com/api/youtube-download"
    base_url = str(request.base_url).rstrip("/")
    
    # কোয়ালিটি লিস্ট
    qualities = ["1080p", "720p", "480p", "360p", "240p", "144p", "audio"]
    all_results = []
    video_info = {}

    for q in qualities:
        # প্রতিবার রিকোয়েস্টে নতুন র্যান্ডম কুকি
        timestamp = int(time.time() * 1000)
        ga_id = f"GA1.1.{random.randint(1000000000, 9999999999)}.{int(time.time())}"
        session_id = f"{timestamp}${generate_random_id(5)}$g0$t{timestamp}"
        
        headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
            'Content-Type': "application/json",
            'origin': "https://thesocialcat.com",
            'referer': "https://thesocialcat.com/tools/youtube-video-downloader",
            'Cookie': f"_ga={ga_id}; _ga_ZECYDJ3Y4Y=GS2.1.s{session_id}; dmcfkjn3cdc={generate_random_id(26).lower()}"
        }

        try:
            payload = {"url": url, "format": q}
            response = requests.post(target_api, data=json.dumps(payload), headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                media_url = data.get("mediaUrl")
                
                if media_url:
                    if not video_info:
                        raw_dur = data.get("videoMeta", {}).get("duration", 0)
                        video_info = {
                            "title": data.get("caption", "YouTube Video"),
                            "duration": format_duration(raw_dur),
                            "thumbnail": data.get("thumbnail"),
                            "author": data.get("username"),
                            "dev": "API Dev @Offline_669"
                        }
                    
                    clean_name = clean_filename(video_info["title"])
                    encoded_url = base64.b64encode(media_url.encode()).decode()
                    ext = "mp3" if q == "audio" else "mp4"
                    
                    # প্রক্সি লিঙ্ক জেনারেশন
                    proxy_link = f"{base_url}/file-stream?data={encoded_url}&name={urllib.parse.quote(clean_name)}&ext={ext}"
                    
                    all_results.append({
                        "quality": "MP3 Audio" if q == "audio" else q,
                        "download_url": proxy_link,
                        "type": "audio" if q == "audio" else "video"
                    })
        except:
            continue

    if not all_results:
        return {"ok": False, "message": "No links found"}

    return {
        "ok": True,
        "video_info": video_info,
        "results": all_results
    }

@app.get("/file-stream")
def file_stream(data: str = Query(...), name: str = Query("video"), ext: str = Query("mp4")):
    try:
        real_url = base64.b64decode(data).decode()
        req = requests.get(real_url, stream=True, timeout=120)
        
        headers = {
            "Content-Disposition": f'attachment; filename="{name}.{ext}"',
            "Content-Type": "audio/mpeg" if ext == "mp3" else "video/mp4"
        }

        def generate():
            for chunk in req.iter_content(chunk_size=1024 * 512):
                if chunk: yield chunk

        return StreamingResponse(generate(), headers=headers)
    except Exception:
        raise HTTPException(status_code=500, detail="Transfer failed")
