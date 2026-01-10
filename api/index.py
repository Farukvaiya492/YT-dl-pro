import httpx
import urllib.parse
import re
from fastapi import FastAPI, Query, Request
from fastapi.responses import StreamingResponse

app = FastAPI()

# আপনার প্রোভাইড করা কুকি এখানে আপডেট করে নিন
COOKIE = "BRANDS_DEFAULT_LANDING_VERSION=4; BRANDS_SMALL_BRANDS_LANDING_VERSION=2; BRANDS_UGC_LANDING_VERSION=2; mp_16cbc705ab859c1f4e2db274a18b0696_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A19ba8c08ea510a7-015d6e8aa6b7a3-4f6f762b-4eb16-19ba8c08ea510a8%22%2C%22%24device_id%22%3A%20%2219ba8c08ea510a7-015d6e8aa6b7a3-4f6f762b-4eb16-19ba8c08ea510a8%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%2C%22source%22%3A%20%22unknown%22%7D; AMP_MKTG_8cc66ffd0f=JTdCJTdE; _fbp=fb.1.1768062752582.257824970208281922; _tt_enable_cookie=1; _ttp=01KEMC163EX38R4MP15Q3AE1EF_.tt.1; AMP_8cc66ffd0f=JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjJhNzM1YzY5My00ZTQ0LTRhZjUtYmUwNy01MDBjNmQ4ODEyZjglMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzY4MDYyNzUxNTA5JTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTc2ODA2Mjc2NDk0OCUyQyUyMmxhc3RFdmVudElkJTIyJTNBNiUyQyUyMnBhZ2VDb3VudGVyJTIyJTNBMSU3RA==; ttcsid_CFC1MRRC77U0H42CQU6G=1768062752928::C0116f2Z-5GiLkiEtXUp.1.1768062775044.0; ttcsid=1768062752932::9GQeg_bHdRwJqFbAMoJu.1.1768062775045.0"

@app.get("/")
async def home():
    return {"message": "YouTube Downloader API is Running", "endpoint": "/download?url=YOUR_URL"}

# টাইটেল থেকে অবৈধ ক্যারেক্টার মুছে ফেলার ফাংশন
def sanitize_filename(filename: str):
    # শুধু ইংরেজি অক্ষর, বাংলা অক্ষর, সংখ্যা, স্পেস এবং ড্যাশ/আন্ডারস্কোর রাখা হবে
    return re.sub(r'[^\w\s\u0980-\u09FF\.\-]', '', filename).strip()

# অডিও প্রক্সি এন্ডপয়েন্ট (টাইটেল সহ)
@app.get("/proxy-audio")
async def proxy_audio(url: str, title: str = "audio"):
    async def stream_generator():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", url, follow_redirects=True) as response:
                async for chunk in response.aiter_bytes(chunk_size=1024 * 64):
                    yield chunk
    
    # টাইটেল ক্লিন করা
    safe_title = sanitize_filename(title)
    if not safe_title:
        safe_title = "downloaded_audio"
        
    return StreamingResponse(
        stream_generator(),
        media_type="audio/mpeg",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.mp3"'}
    )

@app.get("/download")
async def get_video_links(request: Request, url: str = Query(..., description="YouTube Video URL")):
    target_api = "https://thesocialcat.com/api/youtube-download"
    base_url = str(request.base_url).rstrip("/")
    
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
        'Content-Type': "application/json",
        'origin': "https://thesocialcat.com",
        'referer': "https://thesocialcat.com/tools/youtube-video-downloader",
        'Cookie': COOKIE
    }

    qualities = ["1080p", "720p", "480p", "360p", "240p", "144p", "audio"]
    all_links = []
    video_info = {}

    async with httpx.AsyncClient() as client:
        for q in qualities:
            payload = {"url": url, "format": q}
            try:
                response = await client.post(target_api, json=payload, headers=headers, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    media_url = data.get('mediaUrl')
                    caption = data.get('caption', 'audio')
                    
                    if not video_info:
                        video_info = {
                            "title": caption,
                            "thumbnail": data.get('thumbnail'),
                            "author": data.get('username')
                        }
                    
                    if media_url:
                        if q == "audio":
                            # ক্যাপশন এনকোড করে প্রক্সি লিঙ্কে পাঠানো হচ্ছে
                            encoded_caption = urllib.parse.quote(caption)
                            final_url = f"{base_url}/proxy-audio?url={urllib.parse.quote(media_url)}&title={encoded_caption}"
                            
                            all_links.append({
                                "quality": "MP3 Audio (High Quality)",
                                "download_url": final_url,
                                "type": "audio",
                                "ext": "mp3"
                            })
                        else:
                            all_links.append({
                                "quality": q,
                                "download_url": media_url,
                                "type": "video",
                                "ext": "mp4"
                            })
            except Exception as e:
                print(f"Error fetching {q}: {e}")
                continue

    return {
        "success": True,
        "video_info": video_info,
        "results": all_links
    }
