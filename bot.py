import os
import json
import random
import requests
import PIL.Image

if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import moviepy.video.fx.all as vfx

# ==========================================
# 1. SETUP
# ==========================================
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

with open('quotes.json', 'r', encoding='utf-8') as f:
    quotes_list = json.load(f)

todays_quote = random.choice(quotes_list)
nature_keyword = todays_quote['background_keyword']
quote_text = todays_quote['quote']
caption = todays_quote['caption']

# ==========================================
# 2. TEXT FORMATTING
# ==========================================
if "//" in quote_text:
    parts = quote_text.split("//")
    left_part, right_part = parts[0].strip(), parts[1].strip()
else:
    words = quote_text.split()
    mid = len(words) // 2
    left_part, right_part = " ".join(words[:mid]), " ".join(words[mid:])

def make_two_lines(text):
    words = text.split()
    if len(words) <= 2: return text
    mid = len(words) // 2
    return " ".join(words[:mid]) + "\n" + " ".join(words[mid:])

left_text = make_two_lines(left_part)
right_text = make_two_lines(right_part)

# ==========================================
# 3. PEXELS API (Lush Green & Blue Only)
# ==========================================
headers = {"Authorization": PEXELS_API_KEY}
search_query = f"{nature_keyword} lush green forest vivid blue sky -snow -desert -sand -brown"
search_url = f"https://api.pexels.com/videos/search?query={search_query}&orientation=landscape&size=large&per_page=15"

response = requests.get(search_url, headers=headers)
video_data = response.json()

if not video_data.get('videos'):
    fallback_url = "https://api.pexels.com/videos/search?query=vivid+blue+sky+green+forest&orientation=landscape&per_page=5"
    video_data = requests.get(fallback_url, headers=headers).json()

selected_video = random.choice(video_data['videos'])
video_url = selected_video['video_files'][0]['link']

with open("bg_video.mp4", "wb") as f:
    f.write(requests.get(video_url).content)

# ==========================================
# 4. VIDEO PROCESSING
# ==========================================
video = VideoFileClip("bg_video.mp4").subclip(0, 5.5).resize(height=720) 
video = video.fx(vfx.colorx, 0.5) # Darker for cinematic look

if os.path.exists("bgm.mp3"):
    try:
        audio = AudioFileClip("bgm.mp3").subclip(0, 5.5)
        video = video.set_audio(audio)
    except:
        pass

base_text_settings = {
    'fontsize': 32,
    'color': '#FFFFE0', # Creamy Yellow
    'font': 'Georgia-Italic',
    'method': 'caption',
    'size': (video.w * 0.4, None) 
}

txt_left = TextClip(left_text, align='West', **base_text_settings).set_duration(video.duration)
txt_left = txt_left.set_position((video.w * 0.10, 'center'))

txt_right = TextClip(right_text, align='East', **base_text_settings).set_duration(video.duration)
txt_right = txt_right.set_position((video.w * 0.50, 'center'))

# ==========================================
# 5. EXPORT & SEND (Cleaned up logic)
# ==========================================
final_video = CompositeVideoClip([video, txt_left, txt_right])
final_video.write_videofile("final_reel.mp4", fps=24, codec="libx264", audio_codec="aac", logger=None)

telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
with open("final_reel.mp4", "rb") as vid:
    files = {'video': vid}
    payload = {'chat_id': CHAT_ID, 'caption': caption}
    requests.post(telegram_url, data=payload, files=files)

print("🚀 Green & Blue Aesthetic Horizontal Video sent!")
