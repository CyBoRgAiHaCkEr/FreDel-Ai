import streamlit as st
import os, numpy as np, requests, time, json
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq
from gtts import gTTS

# --- 1. CONFIG & SYSTEM STATE ---
st.set_page_config(page_title="FreDèlAi 2026", page_icon="🤖", layout="wide")

for key in ["brain_memory", "messages", "patterns"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else ("" if key == "brain_memory" else {})

# --- 2. THE RESILIENT API ENGINE ---
def call_hf_api(prompt, model_id):
    # Using the DIRECT endpoint (faster for free tier than the Router)
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}", "X-Wait-For-Model": "true"}
    
    # Aggressive 3-strike retry with short wait
    for i in range(3):
        try:
            resp = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=60)
            if resp.status_code == 200 and len(resp.content) > 500:
                return resp.content
            if resp.status_code == 503: # Model is loading
                st.toast(f"⏳ Waking up {model_id.split('/')[-1]}...")
                time.sleep(10) # Give it time to load into GPU
            else:
                break
        except:
            continue
    return None

# --- 3. SIDEBAR CONTROLS ---
with st.sidebar:
    st.title("🤖 FreDèlAi Core")
    
    # Health Monitor
    if st.button("🩺 Check API Health"):
        test = call_hf_api("test", "runwayml/stable-diffusion-v1-5")
        st.success("✅ Connected") if test else st.error("❌ Servers Busy")

    st.divider()
    # File Sync
    files = st.file_uploader("Upload Docs", type=["pdf","png","jpg","jpeg"], accept_multiple_files=True)
    if st.button("⚡ Sync Knowledge"):
        reader = easyocr.Reader(['fr', 'en'], gpu=False)
        for f in files:
            if "pdf" in f.type:
                with pdfplumber.open(f) as pdf:
                    txt = " ".join([p.extract_text() or "" for p in pdf.pages])
            else:
                img = np.array(Image.open(f))
                txt = " ".join(reader.readtext(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), detail=0))
            st.session_state.brain_memory += f"\n[{f.name}]: {txt}"
        st.success("Knowledge Ingested!")

# --- 4. CHAT INTERFACE ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command FreDèlAi..."):
    # Pattern Logic (e.g. apple=red_ball)
    if "=" in prompt and len(prompt.split("=")) == 2:
        k, v = prompt.split("=")
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast("Learned!")

    display_p = prompt
    for k, v in st.session_state.patterns.items():
        if k in prompt.lower(): prompt = prompt.lower().replace(k, v)

    st.session_state.messages.append({"role": "user", "content": display_p})
    with st.chat_message("user"): st.markdown(display_p)

    with st.chat_message("assistant"):
        # IMAGE: SD-Turbo is 4x faster than base SDXL
        if any(x in display_p.lower() for x in ["draw", "image", "paint"]):
            with st.spinner("🎨 Quick Painting..."):
                res = call_hf_api(prompt, "stabilityai/sdxl-turbo")
                if res: st.image(res)
                else: st.warning("Hugging Face queue is full. Try again in 10s.")
        
        # VIDEO: Zeroscope is the only reliable free video model in 2026
        elif "video" in display_p.lower():
            with st.status("🎥 Rendering (Zeroscope)...") as s:
                res = call_hf_api(prompt, "vdo/zeroscope_v2_576w")
                if res:
                    st.video(res)
                    s.update(label="Done!", state="complete")
                else:
                    s.update(label="Server Busy", state="error")
        
        # TEXT: Groq (Llama 3.3)
        else:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            ctx = f"Brain: {st.session_state.brain_memory[:2000]}"
            r = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role":"system","content":f"You are FreDèlAi. {ctx}"}] + st.session_state.messages
            )
            ans = r.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            if "speak" in display_p.lower():
                gTTS(text=ans[:300], lang='fr').save("v.mp3")
                st.audio("v.mp3", autoplay=True)
