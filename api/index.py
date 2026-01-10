import httpx
import urllib.parse
import io
import re
from fastapi import FastAPI, Query, Request
from fastapi.responses import StreamingResponse
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, APIC, error

app = FastAPI()

COOKIE = "BRANDS_DEFAULT_LANDING_VERSION=4; BRANDS_SMALL_BRANDS_LANDING_VERSION=2; BRANDS_UGC_LANDING_VERSION=2; mp_16cbc705ab859c1f4e2db274a18b0696_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A19ba8c08ea510a7-015d6e8aa6b7a3-4f6f762b-4eb16-19ba8c08ea510a8%22%2C%22%24device_id%22%3A%20%2219ba8c08ea510a7-015d6e8aa6b7a3-4f6f762b-4eb16-19ba8c08ea510a8%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%2C%22source%22%3A%20%22unknown%22%7D; AMP_MKTG_8cc66ffd0f=JTdCJTdE; _fbp=fb.1.1768062752582.257824970208281922; _tt_enable_cookie=1; _ttp=01KEMC163EX38R4MP15Q3AE1EF_.tt.1; AMP_8cc66ffd0f=JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjJhNzM1YzY5My00ZTQ0LTRhZjUtYmUwNy01MDBjNmQ4ODEyZjglMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzY4MDYyNzUxNTA5JTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTc2ODA2Mjc2NDk0OCUyQyUyMmxhc3RFdmVudElkJTIyJTNBNiUyQyUyMnBhZ2VDb3VudGVyJTIyJTNBMSU3RA==; ttcsid_CFC1MRRC77U0H42CQU6G=1768062752928::C0116f2Z-5GiLkiEtXUp.1.1768062775044.0; ttcsid=1768062752932::9GQeg_bHdRwJqFbAMoJu.1.1768062775045.0"

# ফাইলের নাম থেকে স্পেশাল ক্যারেক্টার সরানোর ফাংশন (বাংলা সাপোর্ট করবে)
def sanitize_filename(filename: str):
    return re.sub(r'[^\w\s\u0980-\u09FF\.\-]', '', filename).strip()

@app.get("/proxy-audio")
async def proxy_audio(url: str, title: str = "audio", artist: str = "Unknown", thumb: str = None):
    async with httpx.AsyncClient(timeout=None) as client:
        # অডিও ফাইল ডাউনলোড
        audio_res = await client.get(url, follow_redirects=True)
        audio_data = audio_res.content
        
        # থাম্বনেইল ডাউনলোড
        image_data = None
        if thumb:
            try:
                img_res = await client.get(thumb)
                if img_res.status_code == 200:
                    image_data = img_res.content
            except:
                pass

    audio_stream = io.BytesIO(audio_data)
    try:
        # মেটাডেটা সেট করা (টাইটেল, আর্টিস্ট, ইমেজ)
        audio = MP3(audio_stream, ID3=ID3)
        try:
            audio.add_tags()
        except error:
            pass

        audio.tags.add(TIT2(encoding=3, text=title))
        audio.tags.add(TPE1(encoding=3, text=artist))

        if image_data:
            audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=image_data))
        
        output = io.BytesIO()
        audio.save(output)
        output.seek(0)
        
        # এখানে ফাইলের নাম ডাইনামিক করা হয়েছে
        safe_filename = sanitize_filename(title) or "audio"
        return StreamingResponse(
            output, 
            media_type="audio/mpeg", 
            headers={"Content-Disposition": f'attachment; filename="{safe_filename}.mp3"'}
        )
    
    except Exception:
        # এরর হলে অরিজিনাল ফাইলই পাঠানো হবে
        safe_filename = sanitize_filename(title) or "audio"
        return StreamingResponse(
            io.BytesIO(audio_data), 
            media_type="audio/mpeg", 
            headers={"Content-Disposition": f'attachment; filename="{safe_filename}.mp3"'}
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
                    
                    if not video_info:
                        video_info = {
                            "title": data.get('caption'),
                            "thumbnail": data.get('thumbnail'),
                            "author": data.get('username')
                        }
                    
                    if media_url:
                        if q == "audio":
                            # প্রক্সি লিঙ্কে সব তথ্য পাঠানো
                            encoded_title = urllib.parse.quote(video_info['title'] or "Audio")
                            encoded_artist = urllib.parse.quote(video_info['author'] or "Unknown")
                            encoded_thumb = urllib.parse.quote(video_info['thumbnail'] or "")
                            
                            proxy_url = f"{base_url}/proxy-audio?url={urllib.parse.quote(media_url)}&title={encoded_title}&artist={encoded_artist}&thumb={encoded_thumb}"
                            
                            all_links.append({
                                "quality": "MP3 Audio (High Quality)",
                                "download_url": proxy_url,
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
            except:
                continue

    return {"success": True, "video_info": video_info, "results": all_links}

