from fastapi import FastAPI, Query
import requests
import re

app = FastAPI()

def clean_filename(title):
    # ফাইলের নাম থেকে নিষিদ্ধ চিহ্ন বাদ দিয়ে ক্লিন করা
    return re.sub(r'[\\/*?:"<>|]', "", title)

@app.get("/")
async def home():
    return {"message": "YouTube Downloader API is Active", "usage": "/download?url=YOUR_URL"}

@app.get("/download")
async def get_video_links(url: str = Query(..., description="YouTube Video URL")):
    # আমরা একটি শক্তিশালী এবং বিকল্প API ব্যবহার করছি
    # এটি 'vkrdown' এর চেয়ে বেশি স্টেবল
    target_api = f"https://api.cobalt.tools/api/json"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # কোবাল্ট এপিআই এর জন্য পেলোড
    payload = {
        "url": url,
        "vQuality": "1080", # সর্বোচ্চ কোয়ালিটি চেষ্টা করবে
        "aFormat": "mp3",   # অডিওর জন্য mp3
        "isAudioOnly": False
    }

    results = []

    try:
        # ভিডিওর জন্য রিকোয়েস্ট
        response = requests.post(target_api, json=payload, headers=headers, timeout=15)
        data = response.json()

        if data.get("status") == "stream" or data.get("status") == "picker":
            # যদি Picker (অনেকগুলো কোয়ালিটি) আসে
            if data.get("status") == "picker":
                for item in data.get("picker", []):
                    q = item.get("type", "video")
                    link = item.get("url")
                    filename = f"Video_{q}.mp4"
                    results.append({
                        "quality": q,
                        "download_url": link,
                        "filename": filename,
                        "type": "video"
                    })
            else:
                # সিঙ্গেল স্ট্রিম আসলে
                results.append({
                    "quality": "Best Quality",
                    "download_url": data.get("url"),
                    "filename": "video.mp4",
                    "type": "video"
                })

            # অডিওর জন্য আলাদা একটি রিকোয়েস্ট (MP3 নিশ্চিত করতে)
            payload["isAudioOnly"] = True
            audio_response = requests.post(target_api, json=payload, headers=headers, timeout=15)
            audio_data = audio_response.json()
            
            if audio_data.get("url"):
                results.append({
                    "quality": "MP3 Audio",
                    "download_url": audio_data.get("url"),
                    "filename": "audio.mp3",
                    "type": "audio"
                })

            return {
                "success": True,
                "results": results
            }
        else:
            return {"success": False, "message": "Could not fetch media", "details": data}

    except Exception as e:
        return {"success": False, "error": str(e)}
