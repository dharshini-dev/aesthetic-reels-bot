import os
import json
import random
import requests
from datetime import datetime

# 1. PIL ANTIALIAS VERSION FIX
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import moviepy.video.fx.all as vfx

# ==========================================
# 2. SETUP & SECRETS
# ==========================================
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# ==========================================
# 3. LOAD DATA & RANDOM QUOTE SELECTION
# ==========================================
with open('quotes.json', 'r', encoding='utf-8') as f:
    quotes_list = json.load(f)

# Pick a random quote so every reel is unique
todays_quote = random.choice(quotes_list)
nature_keyword = todays_quote['background_keyword']
quote_text = todays_quote['quote']
caption = todays_quote['caption']

# ==========================================
# 4. TEXT FORMATTING (Split & 2-Line Wrap)
# ==========================================
# Remove '//' and split text
if "//" in quote_text:
    parts = quote_text.split("//")
    left_part = parts[0].strip()
    right_part = parts[1].strip()
else:
    words = quote_text.split()
    mid = len(words) // 2
    left_part = " ".join(words[:mid])
    right_part = " ".join(words[mid:])

# Function to force text into 2 readable lines
def make_two_lines(text):
    words = text.split()
    if len(words) <= 2:
        return text
    mid = len(words) // 2
    return " ".join(words[:mid]) + "\n" + " ".join(words[mid:])

left_text = make_two_lines(left_part)
right_text = make_two_lines(right_part)

# ==========================================
# 5. PEXELS API (Peaceful Nature Visuals)
# ==========================================
headers = {"Authorization": PEXELS_API_KEY}
search_query = f"{nature_keyword} peaceful calm nature daylight serene"
search_url = f"https://api.pexels.com/videos/search?query={search_query}&orientation=landscape&size=large&per_page=15"

response = requests.get(search_url, headers=headers)
video_data = response.json()

if not video_data.get('videos'):
    fallback_url = "https://api.pexels.com/videos/search?query=peaceful sunset calm nature&orientation=landscape&size=large&per_page=5"
    video_data = requests.get(fallback_url, headers=headers).json()

selected_video = random.choice(video_data['videos'])
video_url = selected_video['video_files'][0]['link']

with open("bg_video.mp4", "wb") as f:
    f.write(requests.get(video_url).content)

# ==========================================
# 6. VIDEO PROCESSING & RENDERING
# ==========================================
# Resize and ensure even dimensions for Telegram playback
video = VideoFileClip("bg_video.mp4").subclip(0, 5.5).resize(height=720) 
w, h = video.size
video = video.crop(x1=0, y1=0, x2=w - (w % 2), y2=h - (h % 2))

# Subtle darkening for yellow text visibility
video = video.fx(vfx.colorx, 0.7) 

if os.path.exists("bgm.mp3"):
    try:
        audio = AudioFileClip("bgm.mp3").subclip(0, 5.5)
        video = video.set_audio(audio)
    except:
        pass

# Trending Typewriter Aesthetic Text Settings
text_kwargs = {
    'fontsize': 30,             
    'color': 'yellow',           
    'font': 'Courier-Bold', 
    'align': 'center',
    'method': 'caption',
    'size': (video.w * 0.4, None) # Width limit to avoid overlap
}

# Positioning with Instagram Safe Zone (Right 15% space left free)
txt_left = TextClip(left_text, **text_kwargs)
txt_left = txt_left.set_position((video.w * 0.05, 'center')).set_duration(video.duration)

txt_right = TextClip(right_text, **text_kwargs)
txt_right = txt_right.set_position((video.w * 0.45, 'center')).set_duration(video.duration)

# Combine and Export with High-Speed Settings
final_video = CompositeVideoClip([video, txt_left, txt_right])
final_video.write_videofile(
    "final_reel.mp4", 
    fps=24, 
    codec="libx264", 
    audio_codec="aac",
    threads=4,
    preset='fast', 
    ffmpeg_params=['-pix_fmt', 'yuv420p'], # Essential for mobile/telegram playback
    logger=None
)

# ==========================================
# 7. TELEGRAM DELIVERY
# ==========================================
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
with open("final_reel.mp4", "rb") as vid:
    files = {'video': vid}
    data = {'chat_id': CHAT_ID, 'caption': caption}
    requests.post(telegram_url, data=data, files=files)

print("🚀 Cinematic Reel sent successfully!")