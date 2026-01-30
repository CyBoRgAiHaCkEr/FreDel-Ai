import streamlit as st
import os, numpy as np, requests, time, json
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq
from gtts import gTTS

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="FreDèlAi 2026", page_icon="🤖", layout="wide")

# --- 2. THE BRAIN STATE ---
if "brain_memory" not in st.session_state: st.session_state.brain_memory = ""
if "messages" not in st.session_state: st.session_state.messages = []
if "patterns" not in st.session_state: st.session_state.patterns = {}

# --- 3. 2026 RESILIENT ROUTER ENGINE ---
def call_hf_api(prompt, model_id):
    API_URL = f"https://router.huggingface.co/hf-inference/models/{model_id}"
    headers = {
        "Authorization": f"Bearer {st.secrets['HF_TOKEN']}",
        "X-Wait-For-Model": "true",
        "X-Use-Cache": "false"
    }
    
    # 5-Step Retry Loop to wake up cold servers
    for i in range(5):
        try:
            response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=150)
            
            # Success: Return content if it's a real file (not a small JSON error)
            if response.status_code == 200 and len(response.content) > 1000:
                return response.content
            
            # Server Busy/Loading: Wait and Retry
            if response.status_code in [429, 503, 504]:
                wait = (i + 1) * 5
                st.toast(f"🌀 System busy... retrying in {wait}s")
                time.sleep(wait)
                continue
            break
        except Exception:
            time.sleep(2)
            continue
    return None

# --- 4. SIDEBAR: BRAIN PORT & OCR ---
with st.sidebar:
    st.title("🤖 FreDèlAi Control")
    
    # THE BRAIN PORT
    st.subheader("💾 Brain Port")
    brain_json = json.dumps({"mem": st.session_state.brain_memory, "pat": st.session_state.patterns})
    st.download_button("📥 Save Brain", data=brain_json, file_name="fredel_brain.json")
    
    up_brain = st.file_uploader("📤 Load Brain", type="json")
    if up_brain and st.button("🔄 Sync"):
        b = json.load(up_brain)
        st.session_state.brain_memory, st.session_state.patterns = b['mem'], b['pat']
        st.rerun()

    st.divider()
    # PRE-PROCESSED OCR
    is_fr = st.checkbox("French Mode", value=True)
    files = st.file_uploader("Upload Docs", type=["pdf","png","jpg","jpeg"], accept_multiple_files=True)
    if st.button("⚡ Sync Files"):
        reader = easyocr.Reader(['fr', 'en'] if is_fr else ['en'], gpu=False)
        for f in files:
            if "pdf" in f.type:
                with pdfplumber.open(f) as pdf:
                    txt = " ".join([p.extract_text() for p in pdf.pages if p.extract_text() or ""])
            else:
                img = np.array(Image.open(f))
                gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) 
                txt = " ".join(reader.readtext(gray, detail=0, paragraph=True))
            st.session_state.brain_memory += f"\n[{f.name}]: {txt}"
        st.success("Neural Core Updated!")

# --- 5. CHAT TERMINAL ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command FreDèlAi..."):
    # Pattern Logic
    if "=" in prompt and len(prompt.split("=")) == 2:
        k, v = prompt.split("=")
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast("Pattern Learned!")

    display_p = prompt
    for k, v in st.session_state.patterns.items():
        if k in prompt.lower(): prompt = prompt.lower().replace(k, v)

    st.session_state.messages.append({"role": "user", "content": display_p})
    with st.chat_message("user"): st.markdown(display_p)

    with st.chat_message("assistant"):
        # MULTIMEDIA DISPATCHER
        if any(x in display_p.lower() for x in ["draw", "image of", "paint"]):
            with st.spinner("🎨 Turbo-Painting..."):
                img = call_hf_api(prompt, "stabilityai/sdxl-turbo")
                if img: st.image(img)
                else: st.error("Image Server Timed Out. Try again in 10s.")
        
        elif "video" in display_p.lower():
            with st.status("🎥 Rendering (Hunyuan 2026)...", expanded=True) as s:
                vid = call_hf_api(prompt, "tencent/HunyuanVideo")
                if vid: 
                    st.video(vid)
                    s.update(label="Complete!", state="complete")
                else: 
                    s.update(label="Video Server Busy. Try a simpler prompt.", state="error")
        
        else:
            # TEXT ENGINE
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            ctx = f"System Memory: {st.session_state.brain_memory[:2500]}"
            r = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role":"system","content":f"You are FreDèlAi. {ctx}"}] + st.session_state.messages
            )
            ans = r.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            if "speak" in display_p.lower():
                gTTS(text=ans[:300], lang='fr' if is_fr else 'en').save("v.mp3")
                st.audio("v.mp3", autoplay=True)
