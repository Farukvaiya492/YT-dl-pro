from fastapi import FastAPI, Query
import requests
import re

app = FastAPI()

def clean_filename(title):
    # ফাইলের নাম থেকে নিষিদ্ধ চিহ্ন বাদ দেওয়া
    return re.sub(r'[\\/*?:"<>|]', "", title)

@app.get("/")
async def home():
    return {"message": "YouTube Downloader API is Active", "usage": "/download?url=YOUR_URL"}

@app.get("/download")
async def get_video_links(url: str = Query(..., description="YouTube Video URL")):
    # আমরা একটি স্টেবল এবং ফ্রি API ব্যবহার করছি যাতে কুকি লাগে না
    vkr_api = f"https://api.vkrdown.com/api/get?url={url}"
    
    try:
        response = requests.get(vkr_api, timeout=15)
        if response.status_code != 200:
            return {"success": False, "message": "External Server Error"}
            
        data = response.json()
        title = data.get("title", "video")
        safe_title = clean_filename(title)
        medias = data.get("medias", [])
        
        all_results = []
        
        for item in medias:
            quality = item.get("quality")
            download_url = item.get("url")
            extension = item.get("extension")
            
            # অডিও বা MP3 আলাদা করা
            if "audio" in quality.lower() or extension == "mp3":
                filename = f"{safe_title} (Audio).mp3"
                all_results.append({
                    "quality": "MP3 Audio",
                    "download_url": download_url,
                    "filename": filename,
                    "type": "audio"
                })
            else:
                # ভিডিওর সব কোয়ালিটি (1080p, 720p, etc.)
                filename = f"{safe_title} ({quality}).mp4"
                all_results.append({
                    "quality": quality,
                    "download_url": download_url,
                    "filename": filename,
                    "type": "video"
                })

        return {
            "success": True,
            "title": title,
            "thumbnail": data.get("thumbnail"),
            "results": all_results
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
