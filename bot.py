import os
import json
import random
import requests
from datetime import datetime
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import moviepy.video.fx.all as vfx # Video edit pandradhukkaana VFX module

# ==========================================
# 1. SETUP & SECRETS
# ==========================================
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# ==========================================
# 2. LOAD DATA & GET QUOTE
# ==========================================
with open('quotes.json', 'r', encoding='utf-8') as f:
    quotes_list = json.load(f)

# Auto-rotating index based on time
start_date = datetime(2026, 2, 24)
hours_passed = int((datetime.now() - start_date).total_seconds() / 3600)
index = (hours_passed // 12) % len(quotes_list)

todays_quote = quotes_list[index]
nature_keyword = todays_quote['background_keyword']
quote_text = todays_quote['quote']
caption = todays_quote['caption']

# SPLIT QUOTE LOGIC (Left & Right Split for High Retention)
words = quote_text.split()
mid_point = len(words) // 2
left_text = " ".join(words[:mid_point])
right_text = " ".join(words[mid_point:])

print(f"🎬 Left Text: {left_text}")
print(f"🎬 Right Text: {right_text}")

# ==========================================
# 3. PEXELS API FOR HIGH RETENTION
# ==========================================
# RETENTION HACK: Adding "calm cinematic slow" to API query forces it to fetch slow-moving aesthetic videos.
# Landscape orientation creates the cinematic letterbox (black bars top & bottom) on Reels.
headers = {"Authorization": PEXELS_API_KEY}
search_query = f"{nature_keyword} calm cinematic slow"
search_url = f"https://api.pexels.com/videos/search?query={search_query}&orientation=landscape&size=large&per_page=15"

response = requests.get(search_url, headers=headers)
video_data = response.json()

if not video_data.get('videos'):
    print("❌ No videos found. Falling back to default 'slow ocean waves'.")
    fallback_url = "https://api.pexels.com/videos/search?query=calm dark ocean waves slow&orientation=landscape&size=large&per_page=5"
    video_data = requests.get(fallback_url, headers=headers).json()

selected_video = random.choice(video_data['videos'])
video_url = selected_video['video_files'][0]['link']

# Download video
with open("bg_video.mp4", "wb") as f:
    f.write(requests.get(video_url).content)
print("✅ Cinematic nature video downloaded.")

# ==========================================
# 4. VIDEO EDITING & VFX (Darkening + Yellow Font)
# ==========================================
# Load video and trim to exactly 5.5 seconds (High retention loop duration)
video = VideoFileClip("bg_video.mp4").subclip(0, 5.5)

# VFX AUTO-DIM: Reduces video brightness by 50% so the Yellow font stands out on ANY video.
video = video.fx(vfx.colorx, 0.5)

# TEXT SETTINGS: Yellow color + 3px Black Stroke (Makes it glow/pop perfectly)
# Audio file irukka nu check pandrom
if os.path.exists("bgm.mp3"):
    print("🎵 Adding background music...")
    audio = AudioFileClip("bgm.mp3").subclip(0, 5.5)
    video = video.set_audio(audio)
else:
    print("⚠️ bgm.mp3 not found! Sending video without audio.")
    
text_kwargs = {
    'fontsize': 50,
    'color': 'yellow',
    'stroke_color': 'black',
    'stroke_width': 3,
    'font': 'Georgia', # Classy poetic font
    'method': 'caption',
    'size': (video.w * 0.4, None) # Each text block takes 40% of screen width
}

# Left Side Text
txt_left = TextClip(left_text, align='West', **text_kwargs)
txt_left = txt_left.set_position((video.w * 0.05, 'center')).set_duration(video.duration)

# Right Side Text
txt_right = TextClip(right_text, align='East', **text_kwargs)
txt_right = txt_right.set_position((video.w * 0.55, 'center')).set_duration(video.duration)

# Add Aesthetic BGM
audio = AudioFileClip("bgm.mp3").subclip(0, 5.5)
video = video.set_audio(audio)

# Combine dark background with glowing text
final_video = CompositeVideoClip([video, txt_left, txt_right])
final_video.write_videofile("final_reel.mp4", fps=30, codec="libx264", audio_codec="aac")

# ==========================================
# 5. SEND TO TELEGRAM
# ==========================================
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
with open("final_reel.mp4", "rb") as vid:
    files = {'video': vid}
    data = {'chat_id': CHAT_ID, 'caption': caption}
    requests.post(telegram_url, data=data, files=files)

print("🚀 Cinematic Reel successfully delivered to Telegram!")