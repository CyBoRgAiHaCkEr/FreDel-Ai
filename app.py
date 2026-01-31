import streamlit as st
import os, numpy as np, requests, time, json, base64
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq
from gtts import gTTS

# --- 1. SETTINGS ---
st.set_page_config(page_title="FreDèlAi Infinity", page_icon="🤖", layout="wide")

if "messages" not in st.session_state: st.session_state.messages = []
if "brain_memory" not in st.session_state: st.session_state.brain_memory = ""
if "patterns" not in st.session_state: st.session_state.patterns = {}

# --- 2. CACHE-BUSTING IMAGE ENGINE ---
def get_safe_image(prompt):
    clean_p = prompt.replace(" ", "%20")
    # We add a 'Buster' ID that changes every millisecond
    buster_id = str(int(time.time() * 1000))
    
    # We cycle models to find an unblocked one
    models = ["flux", "turbo", "any-dark"]
    
    for model in models:
        url = f"https://gen.pollinations.ai/image/{clean_p}?model={model}&seed={buster_id}&nologo=true&cache={buster_id}"
        try:
            headers = {'User-Agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) {buster_id}'}
            resp = requests.get(url, timeout=25, headers=headers)
            
            # If the image is small, it's the "Limit Reached" placeholder. We reject it.
            if resp.status_code == 200 and len(resp.content) > 15000:
                b64 = base64.b64encode(resp.content).decode()
                return f'<img src="data:image/png;base64,{b64}" style="width:100%; border-radius:15px; border: 2px solid #00ffcc;">'
        except:
            continue
    return "⚠️ **System Shield Active.** The server is forcing a limit. Wait 30s for the shield to drop."

# --- 3. SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.jpg"): st.image("logo.jpg", use_container_width=True)
    st.title("🤖 FreDèlAi")
    st.divider()
    is_fr = st.toggle("French Mode", value=False)
    
    # Memory Sync
    files = st.file_uploader("Sync Knowledge", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("⚡ Update Brain"):
        reader = easyocr.Reader(['en', 'fr'] if is_fr else ['en'], gpu=False)
        for f in files:
            if "pdf" in f.type:
                with pdfplumber.open(f) as pdf:
                    txt = " ".join([p.extract_text() or "" for p in pdf.pages])
            else:
                img = np.array(Image.open(f))
                txt = " ".join(reader.readtext(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), detail=0))
            st.session_state.brain_memory = (st.session_state.brain_memory + f"\n[{f.name}]: {txt}")[-4000:]
        st.success("Brain Updated!")

# --- 4. CHAT ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Command FreDèlAi..."):
    # Pattern Logic
    if "=" in prompt:
        k, v = prompt.split("=")
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast("Learned!")

    display_p = prompt
    for k, v in st.session_state.patterns.items():
        if k in prompt.lower(): prompt = prompt.lower().replace(k, v)

    st.session_state.messages.append({"role": "user", "content": display_p})
    with st.chat_message("user"): st.markdown(display_p)

    with st.chat_message("assistant"):
        if any(x in display_p.lower() for x in ["draw", "image", "paint"]):
            with st.spinner("🎨 Breaking Cache..."):
                img_html = get_safe_image(prompt)
                st.markdown(img_html, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": img_html})
        else:
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                r = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"system","content":f"You are FreDèlAi. Context: {st.session_state.brain_memory[-1000:]}"}] + st.session_state.messages[-5:]
                )
                ans = r.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                if "speak" in display_p.lower():
                    gTTS(text=ans[:300], lang='fr' if is_fr else 'en').save("v.mp3")
                    st.audio("v.mp3", autoplay=True)
            except:
                st.error("Wait 60s for API reset.")
