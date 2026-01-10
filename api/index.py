import httpx
import urllib.parse
import re
from fastapi import FastAPI, Query, Request
from fastapi.responses import StreamingResponse

app = FastAPI()

COOKIE = "BRANDS_DEFAULT_LANDING_VERSION=4; BRANDS_SMALL_BRANDS_LANDING_VERSION=2; BRANDS_UGC_LANDING_VERSION=2; mp_16cbc705ab859c1f4e2db274a18b0696_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A19ba8c08ea510a7-015d6e8aa6b7a3-4f6f762b-4eb16-19ba8c08ea510a8%22%2C%22%24device_id%22%3A%20%2219ba8c08ea510a7-015d6e8aa6b7a3-4f6f762b-4eb16-19ba8c08ea510a8%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%2C%22source%22%3A%20%22unknown%22%7D; AMP_MKTG_8cc66ffd0f=JTdCJTdE; _fbp=fb.1.1768062752582.257824970208281922; _tt_enable_cookie=1; _ttp=01KEMC163EX38R4MP15Q3AE1EF_.tt.1; AMP_8cc66ffd0f=JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjJhNzM1YzY5My00ZTQ0LTRhZjUtYmUwNy01MDBjNmQ4ODEyZjglMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzY4MDYyNzUxNTA5JTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTc2ODA2Mjc2NDk0OCUyQyUyMmxhc3RFdmVudElkJTIyJTNBNiUyQyUyMnBhZ2VDb3VudGVyJTIyJTNBMSU3RA==; ttcsid_CFC1MRRC77U0H42CQU6G=1768062752928::C0116f2Z-5GiLkiEtXUp.1.1768062775044.0; ttcsid=1768062752932::9GQeg_bHdRwJqFbAMoJu.1.1768062775045.0"

def clean_filename(filename):
    """ফাইলের নাম থেকে অবৈধ ক্যারেক্টার রিমুভ করার ফাংশন"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

async def data_streamer(target_url: str):
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            async with client.stream("GET", target_url, follow_redirects=True) as response:
                async for chunk in response.aiter_bytes(chunk_size=32768): # ৩২ কেবি চাঙ্ক
                    yield chunk
        except Exception:
            pass

@app.get("/proxy-file")
async def proxy_file(url: str, title: str = "video", ext: str = "mp4"):
    # ক্যাপশন বা টাইটেলকে ক্লিন করে ফাইলের নাম বানানো
    safe_title = clean_filename(title)
    media_type = "audio/mpeg" if ext == "mp3" else "video/mp4"
    
    return StreamingResponse(
        data_streamer(url),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_title}.{ext}"',
            "Cache-Control": "no-cache"
        }
    )

@app.get("/download")
async def get_video_links(request: Request, url: str = Query(...)):
    target_api = "https://thesocialcat.com/api/youtube-download"
    base_url = str(request.base_url).rstrip("/")
    
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        'Content-Type': "application/json",
        'Cookie': COOKIE
    }

    qualities = ["1080p", "720p", "480p", "360p", "audio"]
    final_results = []
    video_info = {}

    async with httpx.AsyncClient() as client:
        for q in qualities:
            try:
                payload = {"url": url, "format": q}
                response = await client.post(target_api, json=payload, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    media_url = data.get('mediaUrl')
                    caption = data.get('caption', 'video') # এটিই গানের টাইটেল
                    
                    if not video_info:
                        video_info = {
                            "title": caption,
                            "thumbnail": data.get('thumbnail'),
                            "author": data.get('username')
                        }
                    
                    if media_url:
                        ext = "mp3" if q == "audio" else "mp4"
                        # টাইটেলটি এনকোড করে প্রক্সি লিঙ্কে পাঠানো হচ্ছে
                        encoded_title = urllib.parse.quote(caption)
                        encoded_media_url = urllib.parse.quote(media_url)
                        
                        proxy_link = f"{base_url}/proxy-file?url={encoded_media_url}&title={encoded_title}&ext={ext}"
                        
                        final_results.append({
                            "quality": "Audio MP3" if q == "audio" else q,
                            "download_url": proxy_link
                        })
            except:
                continue

    return {"success": True, "video_info": video_info, "results": final_results}
