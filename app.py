import streamlit as st
import requests
import os
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
import numpy as np
from moviepy.editor import VideoClip, AudioFileClip

st.set_page_config(page_title="Quran Video Maker", layout="centered")

# تحميل الخط العربي (مهم جداً لعدم ظهور مربعات)
@st.cache_data
def download_font():
    url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Bold.ttf"
    r = requests.get(url)
    with open("font.ttf", "wb") as f:
        f.write(r.content)

download_font()

st.title("🎬 صانع ريلز القرآن الآلي")

# مدخلات المستخدم
sura = st.number_input("رقم السورة", 1, 114, 1)
aya = st.number_input("رقم الآية", 1, 286, 1)

if st.button("صناعة الفيديو الآن 🚀"):
    try:
        with st.spinner("جاري معالجة الفيديو..."):
            # 1. جلب النص
            res = requests.get(f"https://api.alquran.cloud/v1/ayah/{sura}:{aya}/ar.alafasy").json()
            text = res['data']['text']
            
            # 2. جلب الصوت
            audio_url = f"https://everyayah.com/data/Alafasy_128kbps/{str(sura).zfill(3)}{str(aya).zfill(3)}.mp3"
            audio_data = requests.get(audio_url).content
            with open("temp_audio.mp3", "wb") as f:
                f.write(audio_data)

            # 3. وظيفة رسم الإطار (لتجنب أخطاء السيرفر)
            def make_frame(t):
                img = Image.new('RGB', (720, 1280), color=(0, 0, 0))
                draw = ImageDraw.Draw(img)
                reshaped = arabic_reshaper.reshape(text)
                bidi_text = get_display(reshaped)
                font = ImageFont.truetype("font.ttf", 50)
                bbox = draw.textbbox((0, 0), bidi_text, font=font)
                draw.text(((720-(bbox[2]-bbox[0]))/2, (1280-(bbox[3]-bbox[1]))/2), bidi_text, font=font, fill="white")
                return np.array(img)

            # 4. إنتاج الفيديو
            audio_clip = AudioFileClip("temp_audio.mp3")
            video_clip = VideoClip(make_frame, duration=audio_clip.duration)
            video_clip = video_clip.set_audio(audio_clip)
            
            video_clip.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac")
            
            st.video("final.mp4")
            with open("final.mp4", "rb") as file:
                st.download_button("تحميل الفيديو جاهز للنشر 📥", data=file, file_name="quran_reel.mp4")

    except Exception as e:
        st.error(f"حدث خطأ: {e}")
