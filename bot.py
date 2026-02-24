import requests
from moviepy.editor import *
from moviepy.config import change_settings
import json, random, os
from datetime import datetime

# ==========================================
# 1. SETUP
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
# 2. LOAD DATA (SEQUENTIAL ORDER)
# ==========================================
with open('quotes.json', 'r', encoding='utf-8') as f:
    quotes_list = json.load(f)

# Set the start date (Year, Month, Day)
start_date = datetime(2026, 2, 24) 
days_passed = (datetime.now() - start_date).days

# Calculate index (Loops back to 0 if it reaches the end of the list)
index = days_passed % len(quotes_list)

todays_quote = quotes_list[index]
full_keyword = todays_quote['background_keyword']

print(f"📄 Fetching Quote #{index + 1} from quotes.json")

# ==========================================
# 3. SECURE VIDEO FETCH (Filter by Duration)
# ==========================================
headers = {"Authorization": PEXELS_API_KEY}
search_query = f"{full_keyword} aesthetic nature minimalist lonely"
# Added &min_duration=10 to ensure we get longer videos
v_url = f"https://api.pexels.com/videos/search?query={search_query}&orientation=portrait&per_page=15&min_duration=10"

v_data = requests.get(v_url, headers=headers).json()['videos']
selected_video = random.choice(v_data)

video_files = selected_video['video_files']
video_link = sorted(video_files, key=lambda x: x['width'], reverse=True)[0]['link']

raw_path = f"raw_footage/{short_name}.mp4"
with open(raw_path, 'wb') as f:
    f.write(requests.get(video_link).content)

# Audio
music_path = f"temp_audio/{short_name}.mp3"
stable_audio_url = "https://www.bensound.com/bensound-music/bensound-dreams.mp3"
try:
    r = requests.get(stable_audio_url, timeout=10)
    with open(music_path, 'wb') as f: f.write(r.content)
except: pass

# ==========================================
# 4. VIRAL LOOP EDITING (5.5s Duration)
# ==========================================
raw_clip = VideoFileClip(raw_path)

final_duration = min(5.5, raw_clip.duration - 0.5) 

bg = raw_clip.subclip(0, final_duration).resize(height=1920).crop(x_center=540, width=1080)
overlay = ColorClip(size=(1080, 1920), color=(0,0,0)).set_opacity(0.70).set_duration(final_duration)

final_bg = CompositeVideoClip([bg, overlay]).fadein(0.5).fadeout(0.5)

font_p = "static/Montserrat-Medium.ttf" 

txt = TextClip(todays_quote['quote'], fontsize=35, color='white', font=font_p, method='caption', size=(850, None), align='West', interline=12)
txt = txt.set_start(0.5).set_duration(final_duration - 1.0).fadein(0.5).fadeout(0.5).set_position(('center', 750))

watermark = TextClip("@shiinnnnni", fontsize=22, color='#FFFFFF', font='Arial', method='caption', size=(800, None), align='center')
watermark = watermark.set_duration(final_duration).set_position(('center', 250)).set_opacity(0.4)

final_vid = CompositeVideoClip([final_bg, txt, watermark])

# ==========================================
# 🎵 SECURE LOCAL AUDIO INTEGRATION
# ==========================================
music_path = "bgm.mp3" # Make sure this file is uploaded to your GitHub repo!

if os.path.exists(music_path):
    print("🎵 Audio found! Syncing with video...")
    try:
        audio = AudioFileClip(music_path).set_duration(final_duration).audio_fadeout(0.5)
        final_vid = final_vid.set_audio(audio)
    except Exception as e:
        print(f"⚠️ Error processing audio: {e}")
else:
    print("⚠️ bgm.mp3 is MISSING in your folder! Rendering silent video.")

# ==========================================
# 5. FAST RENDER & SEND
# ====================================================================================
# 5. FAST RENDER & SEND
# ==========================================
out_path = f"final_reels/{short_name}.mp4"
final_vid.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac", preset='ultrafast', threads=4)

telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
payload = {'chat_id': CHAT_ID, 'caption': todays_quote['caption']}
with open(out_path, 'rb') as video_file:
    requests.post(telegram_url, data=payload, files={'video': video_file})

print(f"✅ HD Aesthetic Reel Sent! Final Duration: {final_duration}s")