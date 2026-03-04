import streamlit as st
import requests
import os
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from arabic_reshaper import reshape
from bidi.algorithm import get_display

# إعدادات واجهة الموقع
st.set_page_config(page_title="مصنع الريلز القرآني", layout="centered")
st.title("🎥 صانع المحتوى القرآني الذكي")

# 1. اختيار البيانات (الربط بـ API القرآن)
st.sidebar.header("إعدادات الفيديو")
sura_num = st.sidebar.number_input("رقم السورة", 1, 114, 1)
aya_num = st.sidebar.number_input("رقم الآية", 1, 286, 1)

reciter = st.sidebar.selectbox("اختر القارئ", [
    ("المنشاوي", "Minshawi_Murattal_128kbps"),
    ("العفاسي", "Alafasy_128kbps"),
    ("عبد الباسط", "Abdul_Basit_Murattal_64kbps")
])

# زر التنفيذ
if st.button("توليد الفيديو الآن 🚀"):
    try:
        with st.spinner("جاري جلب الآية والصوت وتصميم الفيديو..."):
            # جلب النص والتشكيل
            res = requests.get(f"https://api.alquran.cloud/v1/ayah/{sura_num}:{aya_num}/ar.alafasy").json()
            aya_text = res['data']['text']
            
            # جلب رابط الصوت
            audio_url = f"https://everyayah.com/data/{reciter[1]}/{str(sura_num).zfill(3)}{str(aya_num).zfill(3)}.mp3"
            
            # عرض البيانات للمستخدم كمعاينة
            st.write(f"📖 الآية: {aya_text}")
            st.audio(audio_url)
            
            st.info("ملاحظة: لدمج الفيديو النهائي بجودة عالية، يتم رفع هذا الكود على Streamlit Cloud مع ملف الخط العربي.")
            
    except Exception as e:
        st.error(f"حدث خطأ في الاتصال: {e}")
