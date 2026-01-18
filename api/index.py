import httpx
import urllib.parse
import re
import base64
import time
from fastapi import FastAPI, Query, Request
from fastapi.responses import StreamingResponse

app = FastAPI()

# আপনার দেওয়া স্ট্যাটিক কুকি
COOKIE = "BRANDS_DEFAULT_LANDING_VERSION=4; BRANDS_SMALL_BRANDS_LANDING_VERSION=2; BRANDS_UGC_LANDING_VERSION=2; mp_16cbc705ab859c1f4e2db274a18b0696_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A19ba8c08ea510a7-015d6e8aa6b7a3-4f6f762b-4eb16-19ba8c08ea510a8%22%2C%22%24device_id%22%3A%20%2219ba8c08ea510a7-015d6e8aa6b7a3-4f6f762b-4eb16-19ba8c08ea510a8%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%2C%22source%22%3A%20%22unknown%22%7D; AMP_MKTG_8cc66ffd0f=JTdCJTdE; _fbp=fb.1.1768062752582.257824970208281922; _tt_enable_cookie=1; _ttp=01KEMC163EX38R4MP15Q3AE1EF_.tt.1; AMP_8cc66ffd0f=JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjJhNzM1YzY5My00ZTQ0LTRhZjUtYmUwNy01MDBjNmQ4ODEyZjglMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzY4MDYyNzUxNTA5JTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTc2ODA2Mjc2NDk0OCUyQyUyMmxhc3RFdmVudElkJTIyJTNBNiUyQyUyMnBhZ2VDb3VudGVyJTIyJTNBMSU3RA==; ttcsid_CFC1MRRC77U0H42CQU6G=1768062752928::C0116f2Z-5GiLkiEtXUp.1.1768062775044.0; ttcsid=1768062752932::9GQeg_bHdRwJqFbAMoJu.1.1768062775045.0"

def format_duration(seconds: int):
    """সেকেন্ডকে HH:MM:SS ফরম্যাটে রূপান্তর"""
    if not seconds: return "00:00"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

def clean_filename(title: str):
    """টাইটেল থেকে ক্লিন ফাইল নেম তৈরি"""
    return re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')

@app.get("/")
async def home():
    return {"status": "active", "dev": "@Offline_669", "endpoint": "/api?url=LINK"}

# ভিডিও ও অডিওর জন্য উন্নত প্রক্সি (টাইটেলসহ ডাউনলোড হবে)
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
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
        'Content-Type': "application/json",
        'origin': "https://thesocialcat.com",
        'referer': "https://thesocialcat.com/tools/youtube-video-downloader",
        'Cookie': COOKIE
    }

    # আপনার চাহিদা অনুযায়ী 720p এবং audio এর জন্য রিকোয়েস্ট
    formats = ["720p", "audio"]
    results = []
    info = {}

    async with httpx.AsyncClient() as client:
        for fmt in formats:
            try:
                payload = {"url": url, "format": fmt}
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
                        
                        # সম্পূর্ণ ডোমেইনসহ আপনার নিজের প্রক্সি লিঙ্ক
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
