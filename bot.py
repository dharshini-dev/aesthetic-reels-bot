import requests
from moviepy.editor import *
import moviepy.video.fx.all as vfx 
from moviepy.config import change_settings
import json
import random
import os
from datetime import datetime

# ==========================================
# 1. SETUP & FOLDER MANAGEMENT
# ==========================================
# E: Drive ImageMagick path as per your system
change_settings({"IMAGEMAGICK_BINARY": r"E:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})

PEXELS_API_KEY = "xbelfDhDjAasQ2KpQdheZDsJILRqOQ2Qp2w5wrkofweGzy4hYRN5tgBv" 
headers = {"Authorization": PEXELS_API_KEY}

# Folders auto-creation
os.makedirs("raw_footage", exist_ok=True)
os.makedirs("final_reels", exist_ok=True)
os.makedirs("captions", exist_ok=True)

unique_id = datetime.now().strftime("%y%m%d_%H%M%S")
short_name = f"reel_{unique_id}"

# ==========================================
# 2. LOAD LOCAL JSON DATA 
# ==========================================
print("Loading daily mic-drop quote...")
try:
    with open('quotes.json', 'r', encoding='utf-8') as file:
        all_quotes = json.load(file)
    todays_quote = random.choice(all_quotes)
    
    quote_text = todays_quote['quote']
    selected_keyword = todays_quote['background_keyword']
    todays_caption_text = todays_quote['caption']
except Exception as e:
    print(f"❌ JSON Error: {e}")
    exit()

# ==========================================
# 3. FETCH CINEMATIC NATURE VIDEO (PEXELS)
# ==========================================
print(f"Fetching pure nature vibe: {selected_keyword}...")
raw_vid_path = f"raw_footage/{short_name}_raw.mp4"

pexels_url = f"https://api.pexels.com/videos/search?query={selected_keyword}&orientation=portrait&per_page=30"
response = requests.get(pexels_url, headers=headers)

if response.status_code == 200 and len(response.json().get('videos', [])) > 0:
    video_data = random.choice(response.json()['videos'])
    hd_file = next((file for file in video_data['video_files'] if file['height'] >= 1920), video_data['video_files'][0])
    with open(raw_vid_path, 'wb') as handler:
        handler.write(requests.get(hd_file['link']).content)
else:
    print("❌ Pexels API Error! Check your key or internet.")
    exit()

# ==========================================
# 4. VIDEO PROCESSING (75% DARK OVERLAY)
# ==========================================
print("Applying cinematic dark filter...")
bg_video = VideoFileClip(raw_vid_path)
duration = min(8.0, bg_video.duration)

bg_video = bg_video.subclip(0, duration).resize(height=1920).crop(x_center=1080/2, width=1080)
overlay = ColorClip(size=(1080, 1920), color=(0,0,0)).set_opacity(0.75).set_duration(duration)
background = CompositeVideoClip([bg_video, overlay])

# ==========================================
# 5. TYPOGRAPHY (LORA FONT + LEFT ALIGN + BRIGHTER ID)
# ==========================================
print("Applying Typography Magic...")
try:
    # MAIN QUOTE: Lora font, Left-aligned, Fade-in effect
    # Note: Lora font kandippa unga system-la install aagirukkanum
    quote_clip = TextClip(quote_text, 
                          fontsize=30, 
                          color='#F5F5F5', 
                          font='Lora',         # <--- Changed to Lora
                          method='caption', 
                          size=(850, None),    # 850px box makes the left align work perfectly
                          align='West',        # <--- Forces Left Alignment
                          interline=18)     
    
    # Positioned at Upper-Middle (Y=750)
    # Starts at 0.5s, lasts until the end, with a 1.5s FADE-IN
    quote_clip = (quote_clip.set_position(('center', 750))
                            .set_start(0.5) 
                            .set_duration(duration - 0.5)
                            .fadein(1.5)) 
                          
    # CHANNEL ID: Visible Light Grey, Top Header Placement
    channel_name = "@your_channel_name" # <--- UNGA ID INGA MAATHUNGA
    channel_clip = TextClip(channel_name, 
                            fontsize=22, 
                            color='#CCCCCC',     # <--- Brightened Grey so it's visible on dark skies
                            font='Arial', 
                            method='caption', 
                            size=(850, None), 
                            align='center')      
    
    # Top Safe Zone (Y=200), visible from start to end
    channel_clip = channel_clip.set_position(('center', 200)).set_duration(duration)

except Exception as e:
    print(f"❌ Font Error: {e}. 'Lora' font install aagirukka nu check pannunga.")
    exit()

# ==========================================
# 6. AUDIO & FINAL RENDER
# ==========================================
final_vid_path = f"final_reels/{short_name}.mp4"
caption_file_path = f"captions/{short_name}.txt"

print(f"Rendering: {short_name}.mp4 ...")
try:
    audio = AudioFileClip("lofi_beat.mp3").set_duration(duration).audio_fadeout(1.5)
    final_video = CompositeVideoClip([background, quote_clip, channel_clip]).set_audio(audio)
except OSError:
    print("⚠️ Audio not found, rendering silent video.")
    final_video = CompositeVideoClip([background, quote_clip, channel_clip])

final_video.write_videofile(final_vid_path, fps=30, codec="libx264", audio_codec="aac")

# ==========================================
# 7. CAPTION GENERATOR FILE
# ==========================================
print("Creating Caption text file...")
with open(caption_file_path, "w", encoding="utf-8") as f:
    f.write(f"Filename: {short_name}.mp4\n-----------------------------------------\n\n{todays_caption_text}\n")

print(f"\n🎉 ALL DONE!")
print(f"🎬 Video: {final_vid_path}")