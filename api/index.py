from fastapi import FastAPI, Query
import requests
import json
import re

app = FastAPI()

# আপনার দেওয়া সেই সম্পূর্ণ কুকি (সবকিছু অপরিবর্তিত)
COOKIE = "BRANDS_DEFAULT_LANDING_VERSION=4; BRANDS_SMALL_BRANDS_LANDING_VERSION=2; BRANDS_UGC_LANDING_VERSION=2; mp_16cbc705ab859c1f4e2db274a18b0696_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A19ba8c08ea510a7-015d6e8aa6b7a3-4f6f762b-4eb16-19ba8c08ea510a8%22%2C%22%24device_id%22%3A%20%2219ba8c08ea510a7-015d6e8aa6b7a3-4f6f762b-4eb16-19ba8c08ea510a8%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%2C%22source%22%3A%20%22unknown%22%7D; AMP_MKTG_8cc66ffd0f=JTdCJTdE; _fbp=fb.1.1768062752582.257824970208281922; _tt_enable_cookie=1; _ttp=01KEMC163EX38R4MP15Q3AE1EF_.tt.1; AMP_8cc66ffd0f=JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjJhNzM1YzY5My00ZTQ0LTRhZjUtYmUwNy01MDBjNmQ4ODEyZjglMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzY4MDYyNzUxNTA5JTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTc2ODA2Mjc2NDk0OCUyQyUyMmxhc3RFdmVudElkJTIyJTNBNiUyQyUyMnBhZ2VDb3VudGVyJTIyJTNBMSU3RA==; ttcsid_CFC1MRRC77U0H42CQU6G=1768062752928::C0116f2Z-5GiLkiEtXUp.1.1768062775044.0; ttcsid=1768062752932::9GQeg_bHdRwJqFbAMoJu.1.1768062775045.0"

def clean_name(text):
    # ফাইলের নাম থেকে নিষিদ্ধ চিহ্ন বাদ দেওয়া
    return re.sub(r'[\\/*?:"<>|]', "", text)

@app.get("/")
async def home():
    return {"message": "API is Active", "usage": "/download?url=YOUR_URL"}

@app.get("/download")
async def get_video_links(url: str = Query(..., description="YouTube Video URL")):
    target_api = "https://thesocialcat.com/api/youtube-download"
    
    # আপনার দেওয়া অরিজিনাল হেডারস
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 13; M2103K19I Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.7499.34 Mobile Safari/537.36",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': "\"Android\"",
        'origin': "https://thesocialcat.com",
        'referer': "https://thesocialcat.com/tools/youtube-video-downloader",
        'Cookie': COOKIE
    }

    qualities = ["1080p", "720p", "480p", "360p", "240p", "144p", "audio"]
    all_links = []

    for q in qualities:
        payload = {"url": url, "format": q}
        
        try:
            response = requests.post(target_api, data=json.dumps(payload), headers=headers, timeout=12)
            
            if response.status_code == 200:
                data = response.json()
                media_url = data.get('mediaUrl')
                caption = data.get('caption', 'video')
                safe_title = clean_name(caption)
                
                if media_url:
                    if q == "audio":
                        # অডিওর জন্য নাম এবং এক্সটেনশন MP3 করা হলো
                        filename = f"{safe_title} (Audio).mp3"
                        all_links.append({
                            "quality": "MP3 Audio",
                            "download_url": media_url,
                            "filename": filename,
                            "type": "audio"
                        })
                    else:
                        # ভিডিওর জন্য নাম এবং এক্সটেনশন MP4 করা হলো
                        filename = f"{safe_title} ({q}).mp4"
                        all_links.append({
                            "quality": q,
                            "download_url": media_url,
                            "filename": filename,
                            "type": "video"
                        })
        except:
            continue

    return {
        "success": True,
        "results": all_links
    }
