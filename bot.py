import requests
from moviepy.editor import *
from moviepy.config import change_settings
import json, random, os
from datetime import datetime

# ==========================================
# 1. SETUP & PATHS
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

unique_id = datetime.now().strftime("%y%m%d_%H%M%S")
short_name = f"reel_{unique_id}"

# ==========================================
# 2. LOAD DATA
# ==========================================
with open('quotes.json', 'r', encoding='utf-8') as f:
    todays_quote = random.choice(json.load(f))

# ==========================================
# 3. DOWNLOAD VIDEO
# ==========================================
headers = {"Authorization": PEXELS_API_KEY}
url = f"https://api.pexels.com/videos/search?query={todays_quote['background_keyword']}&orientation=portrait&per_page=15"
v_data = requests.get(url, headers=headers).json()['videos']
video_url = random.choice(v_data)['video_files'][0]['link']

raw_path = f"raw_footage/{short_name}.mp4"
with open(raw_path, 'wb') as f:
    f.write(requests.get(video_url).content)

# ==========================================
# 4. EDITING (LOOP VIBE)
# ==========================================
duration = 8.0
bg = VideoFileClip(raw_path).subclip(0, duration).resize(height=1920).crop(x_center=540, width=1080)
overlay = ColorClip(size=(1080, 1920), color=(0,0,0)).set_opacity(0.75).set_duration(duration)
final_bg = CompositeVideoClip([bg, overlay]).fadeout(1)

font_p = "static/Montserrat-Regular.ttf"

# Quote: 1s Fade-in, 1s Fade-out gap
txt = TextClip(todays_quote['quote'], fontsize=40, color='white', font=font_p, method='caption', size=(850, None), align='West')
txt = txt.set_start(1).set_duration(6).fadein(1).fadeout(1).set_position(('center', 800))

# Channel ID: @shiinnnnni
watermark = TextClip("@shiinnnnni", fontsize=22, color='#CCCCCC', font='Arial', method='caption', size=(800, None), align='center')
watermark = watermark.set_duration(duration).set_position(('center', 200)).set_opacity(0.6)

# ==========================================
# 5. RENDER & SEND
# ==========================================
final_vid = CompositeVideoClip([final_bg, txt, watermark])

try:
    audio = AudioFileClip("lofi_beat.mp3").set_duration(duration).audio_fadeout(1)
    final_vid = final_vid.set_audio(audio)
except: pass

out_path = f"final_reels/{short_name}.mp4"
final_vid.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac")

# Telegram Sending with Log
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
payload = {'chat_id': CHAT_ID, 'caption': todays_quote['caption']}

with open(out_path, 'rb') as video_file:
    r = requests.post(telegram_url, data=payload, files={'video': video_file})
    print(f"📡 Status: {r.status_code} | Video sent to @shiinnnnni")