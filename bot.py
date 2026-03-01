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
# SETUP
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
# TEXT WRAPPING
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
# PEXELS API (Lush Green & Deep Blue ONLY)
# ==========================================
headers = {"Authorization": PEXELS_API_KEY}

# Ippo search-la "vivid blue sky" and "lush green forest" highlight panni,
# snow, desert, sand, brown, autumn-ellam thookiytom.
search_query = f"{nature_keyword} lush green vivid blue nature -snow -desert -sand -brown -dry -autumn"
search_url = f"https://api.pexels.com/videos/search?query={search_query}&orientation=landscape&size=large&per_page=15"

response = requests.get(search_url, headers=headers)
video_data = response.json()

if not video_data.get('videos'):
    fallback_url = "https://api.pexels.com/videos/search?query=lush+green+forest+vivid+blue+ocean&orientation=landscape&size=large&per_page=5"
    video_data = requests.get(fallback_url, headers=headers).json()

selected_video = random.choice(video_data['videos'])
video_url = selected_video['video_files'][0]['link']

with open("bg_video.mp4", "wb") as f:
    f.write(requests.get(video_url).content)

# ==========================================
# VIDEO PROCESSING (Landscape 16:9)
# ==========================================
video = VideoFileClip("bg_video.mp4").subclip(0, 5.5).resize(height=720) 

# DARKNESS: 0.5 (50% darkness) - Idhu dhaan green background-la yellow text-ah highlight pannum.
video = video.fx(vfx.colorx, 0.5) 

if os.path.exists("bgm.mp3"):
    try:
        audio = AudioFileClip("bgm.mp3").subclip(0, 5.5)
        video = video.set_audio(audio)
    except: pass

# PREMIUM FONT SETTINGS
base_text_settings = {
    'fontsize': 32,
    'color': '#FFFF88', # Light Golden Yellow (Cinematic feel)
    'font': 'Georgia-Italic', # Elegant and Thin
    'method': 'caption',
    'size': (video.w * 0.4, None) 
}

# Horizontal-la text space adhigham, so padding koraikalaam.
txt_left = TextClip(left_text, align='West', **base_text_settings).set_duration(video.duration)
txt_left = txt_left.set_position((video.w * 0.15, 'center'))

txt_right = TextClip(right_text, align='East', **base_text_settings).set_duration(video.duration)
txt_right = txt_right.set_position((video.w * 0.45, 'center'))

# ==========================================
# EXPORT
# ==========================================
final_video = CompositeVideoClip([video, txt_left, txt_right])
final_video.write_videofile("final_reel.mp4", fps=24, codec="libx264", audio_codec="aac", logger=None)
}

# Left side
txt_left = TextClip(left_text, align='West', **base_text_settings)
txt_left = txt_left.set_position((video.w * 0.20, 'center')).set_duration(video.duration)

# Right side
txt_right = TextClip(right_text, align='East', **base_text_settings)
txt_right = txt_right.set_position((video.w * 0.30, 'center')).set_duration(video.duration)

# ... (Export section remains the same)
# ==========================================
# 7. EXPORT & SEND
# ==========================================
final_video = CompositeVideoClip([video, txt_left, txt_right])
final_video.write_videofile(
    "final_reel.mp4", 
    fps=24, 
    codec="libx264", 
    audio_codec="aac",
    threads=4,
    preset='fast', 
    ffmpeg_params=['-pix_fmt', 'yuv420p'], 
    logger=None
)

telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
with open("final_reel.mp4", "rb") as vid:
    files = {'video': vid}
    data = {'chat_id': CHAT_ID, 'caption': caption}
    requests.post(telegram_url, data=data, files=files)

print("🚀 Aesthetic Reel (No Drones, Small Georgia Font) sent successfully!")
