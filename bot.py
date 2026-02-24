import requests
from moviepy.editor import *
from moviepy.config import change_settings
import json, random, os
from datetime import datetime

# ==========================================
# 1. CLOUD & LOCAL SETUP
# ==========================================
if os.environ.get('GITHUB_ACTIONS'):
    pass # Linux cloud environment handles this automatically
else:
    change_settings({"IMAGEMAGICK_BINARY": r"E:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})

PEXELS_API_KEY = os.environ.get('PEXELS_API_KEY', "xbelfDhDjAasQ2KpQdheZDsJILRqOQ2Qp2w5wrkofweGzy4hYRN5tgBv")
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

os.makedirs("raw_footage", exist_ok=True)
os.makedirs("final_reels", exist_ok=True)

unique_id = datetime.now().strftime("%y%m%d_%H%M%S")
short_name = f"reel_{unique_id}"

# ==========================================
# 2. LOAD QUOTE & CAPTION
# ==========================================
with open('quotes.json', 'r', encoding='utf-8') as f:
    all_quotes = json.load(f)
    todays_quote = random.choice(all_quotes)

# ==========================================
# 3. DOWNLOAD PEXELS VIDEO
# ==========================================
headers = {"Authorization": PEXELS_API_KEY}
url = f"https://api.pexels.com/videos/search?query={todays_quote['background_keyword']}&orientation=portrait&per_page=15"
response = requests.get(url, headers=headers)
v_data = response.json()['videos']
video_url = random.choice(v_data)['video_files'][0]['link']

raw_path = f"raw_footage/{short_name}.mp4"
with open(raw_path, 'wb') as f:
    f.write(requests.get(video_url).content)

# ==========================================
# 4. VIDEO EDITING & TYPOGRAPHY
# ==========================================
bg = VideoFileClip(raw_path).subclip(0, 8).resize(height=1920).crop(x_center=540, width=1080)
overlay = ColorClip(size=(1080, 1920), color=(0,0,0)).set_opacity(0.75).set_duration(8)
final_bg = CompositeVideoClip([bg, overlay])

font_p = "static/Montserrat-Regular.ttf"

# Quote Text
txt = TextClip(todays_quote['quote'], fontsize=35, color='white', font=font_p, method='caption', size=(850, None), align='West').set_start(0.5).set_duration(7).fadein(1).set_position(('center', 750))
# Channel ID Watermark
watermark = TextClip("@your_channel_name", fontsize=20, color='#CCCCCC', font='Arial', method='caption', size=(800, None), align='center').set_duration(8).set_position(('center', 200))

# ==========================================
# 5. RENDER & TELEGRAM SEND
# ==========================================
final_vid = CompositeVideoClip([final_bg, txt, watermark])
try:
    audio = AudioFileClip("lofi_beat.mp3").set_duration(8)
    final_vid = final_vid.set_audio(audio)
except: 
    pass

out_path = f"final_reels/{short_name}.mp4"
final_vid.write_videofile(out_path, fps=24, codec="libx264")

# Sending video with the SEO caption attached
print("🚀 Sending to Telegram with Caption...")
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
payload = {'chat_id': CHAT_ID, 'caption': todays_quote['caption']}

with open(out_path, 'rb') as video_file:
    requests.post(telegram_url, data=payload, files={'video': video_file})
print("✅ Done!")
# Intha block-ai bot.py-oda kadasila replace pannunga
print("🚀 Attempting to send video to Telegram...")
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
payload = {'chat_id': CHAT_ID, 'caption': todays_quote['caption']}

with open(out_path, 'rb') as video_file:
    r = requests.post(telegram_url, data=payload, files={'video': video_file})
    print(f"📡 Telegram Response: {r.status_code}")
    print(f"💬 Response Text: {r.text}")