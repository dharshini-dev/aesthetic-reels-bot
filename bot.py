import requests
from moviepy.editor import *
from moviepy.config import change_settings
import json, random, os
from datetime import datetime

# ==========================================
# 1. SETUP & OPTIMIZATION
# ==========================================
if os.environ.get('GITHUB_ACTIONS'):
    pass 
else:
    change_settings({"IMAGEMAGICK_BINARY": r"E:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})

PEXELS_API_KEY = os.environ.get('PEXELS_API_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

os.makedirs("raw_footage", exist_ok=True)
os.makedirs("final_reels", exist_ok=True)
os.makedirs("temp_audio", exist_ok=True)

unique_id = datetime.now().strftime("%y%m%d_%H%M%S")
short_name = f"reel_{unique_id}"

# ==========================================
# 2. DATA LOAD 
# ==========================================
with open('quotes.json', 'r', encoding='utf-8') as f:
    todays_quote = random.choice(json.load(f))
    full_keyword = todays_quote['background_keyword']

# ==========================================
# 3. REFINED AESTHETIC SEARCH (NATURE/LONELY)
# ==========================================
headers = {"Authorization": PEXELS_API_KEY}
# Query updated to include minimalist and nature vibes specifically
search_query = f"{full_keyword} aesthetic nature minimalist lonely"
v_url = f"https://api.pexels.com/videos/search?query={search_query}&orientation=portrait&per_page=15"

v_data = requests.get(v_url, headers=headers).json()['videos']
video_link = random.choice(v_data)['video_files'][0]['link']

raw_path = f"raw_footage/{short_name}.mp4"
with open(raw_path, 'wb') as f:
    f.write(requests.get(video_link).content)

# Audio fallback
music_path = f"temp_audio/{short_name}.mp3"
stable_audio_url = "https://www.bensound.com/bensound-music/bensound-dreams.mp3"
try:
    r = requests.get(stable_audio_url, timeout=10)
    with open(music_path, 'wb') as f: f.write(r.content)
except: pass

# ==========================================
# 4. EDITING (0.5s FADES + MINIMAL FONT)
# ==========================================
duration = 8.0
bg = VideoFileClip(raw_path).subclip(0, duration).resize(height=1920).crop(x_center=540, width=1080)
overlay = ColorClip(size=(1080, 1920), color=(0,0,0)).set_opacity(0.75).set_duration(duration)

# Video Fade: 0.5s In and Out for smooth loop
final_bg = CompositeVideoClip([bg, overlay]).fadein(0.5).fadeout(0.5)

font_p = "static/Montserrat-Medium.ttf" 

txt = TextClip(todays_quote['quote'], fontsize=32, color='white', font=font_p, method='caption', size=(800, None), align='West', interline=10)
txt = txt.set_start(0.5).set_duration(7).fadein(0.5).fadeout(0.5).set_position(('center', 800))

watermark = TextClip("@shiinnnnni", fontsize=20, color='#CCCCCC', font='Arial', method='caption', size=(800, None), align='center')
watermark = watermark.set_duration(duration).set_position(('center', 200)).set_opacity(0.5)

final_vid = CompositeVideoClip([final_bg, txt, watermark])

if os.path.exists(music_path):
    try:
        audio = AudioFileClip(music_path).set_duration(duration).audio_fadeout(0.5)
        final_vid = final_vid.set_audio(audio)
    except: pass

# ==========================================
# 5. FAST RENDER & SEND
# ==========================================
out_path = f"final_reels/{short_name}.mp4"
final_vid.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac", preset='ultrafast', threads=4)

telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
payload = {'chat_id': CHAT_ID, 'caption': todays_quote['caption']}
with open(out_path, 'rb') as video_file:
    requests.post(telegram_url, data=payload, files={'video': video_file})

print(f"🚀 Aesthetic Minimalist Reel Sent! Theme: {full_keyword}")