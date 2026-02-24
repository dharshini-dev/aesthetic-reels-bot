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
PIXABAY_API_KEY = "48995383-2d2f88325997a6f23f663189d"

os.makedirs("raw_footage", exist_ok=True)
os.makedirs("final_reels", exist_ok=True)
os.makedirs("temp_audio", exist_ok=True)

unique_id = datetime.now().strftime("%y%m%d_%H%M%S")
short_name = f"reel_{unique_id}"

# ==========================================
# 2. LOAD DATA
# ==========================================
with open('quotes.json', 'r', encoding='utf-8') as f:
    todays_quote = random.choice(json.load(f))
    full_keyword = todays_quote['background_keyword']
    # Simple keyword for music search to avoid API errors
    music_search_keyword = full_keyword.split()[-1] 

# ==========================================
# 3. VIDEO (PEXELS)
# ==========================================
headers = {"Authorization": PEXELS_API_KEY}
v_url = f"https://api.pexels.com/videos/search?query={full_keyword}&orientation=portrait&per_page=15"
v_data = requests.get(v_url, headers=headers).json()['videos']
video_link = random.choice(v_data)['video_files'][0]['link']

raw_path = f"raw_footage/{short_name}.mp4"
with open(raw_path, 'wb') as f:
    f.write(requests.get(video_link).content)

# ==========================================
# 4. AUTO MUSIC (PIXABAY)
# ==========================================
music_path = f"temp_audio/{short_name}.mp3"
backup_url = "https://www.chosic.com/wp-content/uploads/2021/07/Rainy-Day-Lofi-Chill-Background-Music.mp3"

try:
    print(f"🎵 Searching music for: {music_search_keyword}")
    a_url = f"https://pixabay.com/api/audio/?key={PIXABAY_API_KEY}&q={music_search_keyword}&per_page=5"
    response = requests.get(a_url)
    a_res = response.json()

    if a_res.get('hits'):
        audio_link = random.choice(a_res['hits'])['audio']
        with open(music_path, 'wb') as f:
            f.write(requests.get(audio_link).content)
    else:
        raise Exception("No music hits")
except Exception as e:
    print(f"⚠️ Music API failed, using backup lofi. Error: {e}")
    with open(music_path, 'wb') as f:
        f.write(requests.get(backup_url).content)

# ==========================================
# 5. EDITING
# ==========================================
duration = 8.0
bg = VideoFileClip(raw_path).subclip(0, duration).resize(height=1920).crop(x_center=540, width=1080)
overlay = ColorClip(size=(1080, 1920), color=(0,0,0)).set_opacity(0.75).set_duration(duration)
final_bg = CompositeVideoClip([bg, overlay])

font_p = "static/Montserrat-Regular.ttf"
txt = TextClip(todays_quote['quote'], fontsize=40, color='white', font=font_p, method='caption', size=(850, None), align='West')
txt = txt.set_start(1).set_duration(6).fadein(1).fadeout(1).set_position(('center', 800))

watermark = TextClip("@shiinnnnni", fontsize=22, color='#CCCCCC', font='Arial', method='caption', size=(800, None), align='center')
watermark = watermark.set_duration(duration).set_position(('center', 200)).set_opacity(0.6)

final_vid = CompositeVideoClip([final_bg, txt, watermark])
audio = AudioFileClip(music_path).set_duration(duration).audio_fadeout(0.5)
final_vid = final_vid.set_audio(audio)

out_path = f"final_reels/{short_name}.mp4"
final_vid.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac")

# ==========================================
# 6. TELEGRAM SEND
# ==========================================
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
payload = {'chat_id': CHAT_ID, 'caption': todays_quote['caption']}
with open(out_path, 'rb') as video_file:
    requests.post(telegram_url, data=payload, files={'video': video_file})
print("✅ Automated Reel Sent successfully!")