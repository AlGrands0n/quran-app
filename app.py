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

st.set_page_config(page_title="Quran Reels Maker", layout="centered")

@st.cache_data
def download_font():
    url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Bold.ttf"
    try:
        r = requests.get(url)
        with open("font.ttf", "wb") as f:
            f.write(r.content)
    except:
        st.error("خطأ في تحميل الخط، تأكد من اتصال الإنترنت")

download_font()

@st.cache_data
def get_surahs():
    try:
        res = requests.get("https://api.alquran.cloud/v1/surah").json()
        return {item['name']: item['number'] for item in res['data']}
    except:
        return {"الفاتحة": 1}

surahs_dict = get_surahs()

st.title("🌿 صانع ريلز القرآن الاحترافي")
st.write("حسابك: @itsmzajy")

selected_surah_name = st.selectbox("اختر السورة", list(surahs_dict.keys()))
surah_num = surahs_dict[selected_surah_name]

res_surah = requests.get(f"https://api.alquran.cloud/v1/surah/{surah_num}").json()
total_ayas = res_surah['data']['numberOfAyahs']
aya_num = st.number_input(f"رقم الآية (1 إلى {total_ayas})", 1, total_ayas, 1)

reciters = {
    "مشاري العفاسي": "Alafasy_128kbps",
    "عبد الباسط عبد الصمد": "Abdul_Basit_Murattal_64kbps",
    "محمد صديق المنشاوي": "Minshawi_Murattal_128kbps",
    "سعد الغامدي": "Ghamadi_40kbps"
}
selected_reciter = st.selectbox("اختر القارئ", list(reciters.keys()))

if st.button("صناعة الفيديو الاحترافي 🚀"):
    try:
        with st.spinner("جاري جلب البيانات والدمج... قد يستغرق الأمر دقيقة"):
            
            # 1. جلب النص
            res_aya = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah_num}:{aya_num}/ar.alafasy").json()
            raw_text = res_aya['data']['text']
            
            # 2. جلب الصوت
            audio_code = reciters[selected_reciter]
            audio_url = f"https://everyayah.com/data/{audio_code}/{str(surah_num).zfill(3)}{str(aya_num).zfill(3)}.mp3"
            with open("temp_audio.mp3", "wb") as f:
                f.write(requests.get(audio_url).content)
            audio_clip = AudioFileClip("temp_audio.mp3")

            # 3. روابط فيديوهات خلفية قوية جداً (Direct MP4)
            bg_videos = [
                "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/free-nature-video-1.mp4",
                "https://v.ftcdn.net/02/95/94/54/700_F_295945484_S8T9T8Y9KxXG2kE2lS4FpCq7p8XyR2M4_ST.mp4",
                "https://www.w3schools.com/html/mov_bbb.mp4" # رابط تجريبي مستقر جداً
            ]
            
            success = False
            for url in random.sample(bg_videos, len(bg_videos)):
                try:
                    r = requests.get(url, timeout=15)
                    if r.status_code == 200:
                        with open("temp_bg.mp4", "wb") as f:
                            f.write(r.content)
                        if os.path.getsize("temp_bg.mp4") > 50000:
                            success = True
                            break
                except:
                    continue
            
            if not success:
                st.error("المصادر مشغولة حالياً، يرجى إعادة الضغط على الزر.")
                st.stop()

            video_bg = VideoFileClip("temp_bg.mp4")
            
            # معالجة المدة والمقاس
            if video_bg.duration < audio_clip.duration:
                video_bg = video_bg.loop(duration=audio_clip.duration)
            else:
                video_bg = video_bg.subclip(0, audio_clip.duration)

            video_bg = video_bg.resize(height=1920)
            video_bg = video_bg.crop(x_center=video_bg.w/2, width=1080, height=1920)

            # 4. وظيفة رسم النص
            def create_overlay_frame(t):
                img = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                font_aya = ImageFont.truetype("font.ttf", 70)
                font_info = ImageFont.truetype("font.ttf", 35)

                wrapped_lines = textwrap.wrap(raw_text, width=28)
                processed_lines = [get_display(arabic_reshaper.reshape(line)) for line in wrapped_lines]
                full_display_text = "\n".join(processed_lines)

                bbox = draw.multiline_textbbox((0, 0), full_display_text, font=font_aya)
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                
                # خلفية نص شبه شفافة
                draw.rectangle([((1080-w)/2-40, (1920-h)/2-20), ((1080+w)/2+40, (1920+h)/2+20)], fill=(0,0,0,160))
                draw.multiline_text(((1080-w)/2, (1920-h)/2), full_display_text, font=font_aya, fill="white", align="center")

                # حقوق وآية
                info_text = f"سورة {selected_surah_name} | آية {aya_num}"
                info_display = get_display(arabic_reshaper.reshape(info_text))
                draw.text(((1080-draw.textbbox((0,0), info_display, font=font_info)[2])/2, (1920+h)/2 + 70), info_display, font=font_info, fill="#FFD700")

                draw.text(((1080-draw.textbbox((0,0), "@itsmzajy", font=font_info)[2])/2, 1780), "@itsmzajy", font=font_info, fill=(255,255,255,200))
                
                return np.array(img)

            overlay_clip = VideoClip(create_overlay_frame, duration=audio_clip.duration).set_ismask(False)
            
            # 5. الدمج والإنتاج
            final_video = CompositeVideoClip([video_bg, overlay_clip])
            final_video = final_video.set_audio(audio_clip)
            
            output_name = "final_reel.mp4"
            final_video.write_videofile(output_name, fps=24, codec="libx264", audio_codec="aac", temp_audiofile='temp-audio.m4a', remove_temp=True)

            st.video(output_name)
            st.download_button("تحميل الفيديو الآن 📥", open(output_name, "rb"), "itsmzajy_quran.mp4")

    except Exception as e:
        st.error(f"حدث خطأ تقني: {e}")
