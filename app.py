import streamlit as st
import requests
import os
import random
import textwrap
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, VideoClip, CompositeVideoClip

# إعدادات الصفحة
st.set_page_config(page_title="Quran Reels Maker", layout="centered")

# وظيفة تحميل الخط العربي
@st.cache_data
def download_font():
    url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Bold.ttf"
    r = requests.get(url)
    with open("font.ttf", "wb") as f:
        f.write(r.content)

download_font()

# جلب أسماء السور
@st.cache_data
def get_surahs():
    try:
        res = requests.get("https://api.alquran.cloud/v1/surah").json()
        return {item['name']: item['number'] for item in res['data']}
    except:
        return {"الفاتحة": 1}

surahs_dict = get_surahs()

st.title("🌿 صانع ريلز القرآن الاحترافي")
st.write("الحساب الحالي: @itsmzajy")

# واجهة الاختيار
selected_surah_name = st.selectbox("اختر السورة", list(surahs_dict.keys()))
surah_num = surahs_dict[selected_surah_name]

# جلب عدد آيات السورة
res_surah = requests.get(f"https://api.alquran.cloud/v1/surah/{surah_num}").json()
total_ayas = res_surah['data']['numberOfAyahs']
aya_num = st.number_input(f"رقم الآية (من 1 إلى {total_ayas})", 1, total_ayas, 1)

reciters = {
    "مشاري العفاسي": "Alafasy_128kbps",
    "عبد الباسط عبد الصمد": "Abdul_Basit_Murattal_64kbps",
    "محمد صديق المنشاوي": "Minshawi_Murattal_128kbps",
    "سعد الغامدي": "Ghamadi_40kbps"
}
selected_reciter = st.selectbox("اختر القارئ", list(reciters.keys()))

if st.button("صناعة الفيديو الاحترافي 🚀"):
    try:
        with st.spinner("جاري المعالجة والدمج..."):
            
            # 1. جلب النص
            res_aya = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah_num}:{aya_num}/ar.alafasy").json()
            raw_text = res_aya['data']['text']
            
            # 2. جلب الصوت
            audio_code = reciters[selected_reciter]
            audio_url = f"https://everyayah.com/data/{audio_code}/{str(surah_num).zfill(3)}{str(aya_num).zfill(3)}.mp3"
            with open("temp_audio.mp3", "wb") as f:
                f.write(requests.get(audio_url).content)
            audio_clip = AudioFileClip("temp_audio.mp3")

            # 3. جلب فيديو خلفية
            bg_videos = [
                "https://assets.mixkit.co/videos/preview/mixkit-beautiful-mountain-landscape-under-a-blue-sky-5219-large.mp4",
                "https://assets.mixkit.co/videos/preview/mixkit-forest-stream-in-the-sunlight-529-large.mp4"
            ]
            bg_url = random.choice(bg_videos)
            with open("temp_bg.mp4", "wb") as f:
                f.write(requests.get(bg_url).content)
            
            video_bg = VideoFileClip("temp_bg.mp4").subclip(0, audio_clip.duration).resize(height=1920)
            video_bg = video_bg.crop(x_center=video_bg.w/2, width=1080, height=1920)

            # 4. وظيفة رسم النص
            def create_overlay_frame(t):
                img = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                font_aya = ImageFont.truetype("font.ttf", 70)
                font_info = ImageFont.truetype("font.ttf", 35)

                # تقسيم النص (Wrap)
                wrapped_lines = textwrap.wrap(raw_text, width=30)
                processed_lines = [get_display(arabic_reshaper.reshape(line)) for line in wrapped_lines]
                full_display_text = "\n".join(processed_lines)

                # حساب الأبعاد
                bbox = draw.multiline_textbbox((0, 0), full_display_text, font=font_aya)
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                
                # رسم الخلفية والنص
                draw.rectangle([((1080-w)/2-40, (1920-h)/2-20), ((1080+w)/2+40, (1920+h)/2+20)], fill=(0,0,0,140))
                draw.multiline_text(((1080-w)/2, (1920-h)/2), full_display_text, font=font_aya, fill="white", align="center")

                # معلومات السورة واليوزر
                info_text = f"سورة {selected_surah_name} | آية {aya_num}"
                info_display = get_display(arabic_reshaper.reshape(info_text))
                draw.text(((1080-draw.textbbox((0,0), info_display, font=font_info)[2])/2, (1920+h)/2 + 60), info_display, font=font_info, fill="yellow")

                user_display = "@itsmzajy"
                draw.text(((1080-draw.textbbox((0,0), user_display, font=font_info)[2])/2, 1750), user_display, font=font_info, fill=(255,255,255,180))
                
                return np.array(img)

            overlay_clip = VideoClip(create_overlay_frame, duration=audio_clip.duration).set_ismask(False)
            
            # 5. الدمج
            final_video = CompositeVideoClip([video_bg, overlay_clip])
            final_video = final_video.set_audio(audio_clip)
            final_video.write_videofile("final_reel.mp4", fps=20, codec="libx264")

            st.video("final_reel.mp4")
            st.download_button("تحميل الريلز الجاهز ✨", open("final_reel.mp4", "rb"), "itsmzajy_quran.mp4")

    except Exception as e:
        st.error(f"حدث خطأ أثناء المعالجة: {e}")
