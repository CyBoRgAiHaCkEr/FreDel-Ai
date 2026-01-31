import streamlit as st
import os, numpy as np, requests, time, json
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq
from gtts import gTTS

# --- 1. CONFIG & SYSTEM BRAIN ---
st.set_page_config(page_title="FreDèlAi 2026", page_icon="🤖", layout="wide")

# Persistent memory keys
if "brain_memory" not in st.session_state: st.session_state.brain_memory = ""
if "messages" not in st.session_state: st.session_state.messages = []
if "patterns" not in st.session_state: st.session_state.patterns = {}

# --- 2. RESILIENT API ENGINE (503 FIX) ---
def call_hf_api(prompt, model_id):
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {
        "Authorization": f"Bearer {st.secrets['HF_TOKEN']}",
        "X-Wait-For-Model": "true",
        "X-Use-Cache": "false"
    }
    
    # We try 5 times with increasing wait periods to bypass "Server Busy"
    for i in range(5):
        try:
            resp = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=100)
            if resp.status_code == 200 and len(resp.content) > 1000:
                return resp.content
            
            # If 503 (Busy) or 429 (Rate Limit), we wait and retry
            if resp.status_code in [503, 429]:
                wait = (i + 1) * 7 # 7s, 14s, 21s...
                st.toast(f"🌀 Server is waking up... retrying in {wait}s")
                time.sleep(wait)
                continue
            break
        except:
            continue
    return None

# --- 3. SIDEBAR: THE BRAIN PORT & OCR ---
with st.sidebar:
    st.title("🤖 FreDèlAi Control")
    
    # --- DOWNLOAD BRAIN ---
    st.subheader("💾 Export Brain")
    brain_data = {
        "memory": st.session_state.brain_memory,
        "patterns": st.session_state.patterns,
        "history": st.session_state.messages
    }
    st.download_button(
        label="📥 Download .JSON Brain",
        data=json.dumps(brain_data),
        file_name="fredel_brain_2026.json",
        mime="application/json"
    )
    
    # --- UPLOAD BRAIN ---
    st.subheader("📤 Import Brain")
    uploaded_brain = st.file_uploader("Upload a saved Brain file", type="json")
    if uploaded_brain and st.button("🔄 Sync Brain"):
        data = json.load(uploaded_brain)
        st.session_state.brain_memory = data.get("memory", "")
        st.session_state.patterns = data.get("patterns", {})
        st.session_state.messages = data.get("history", [])
        st.success("Brain Synced!")
        st.rerun()

    st.divider()
    # OCR Section
    is_fr = st.checkbox("French Mode", value=True)
    files = st.file_uploader("Sync Docs (PDF/Img)", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("⚡ Process Knowledge"):
        reader = easyocr.Reader(['fr', 'en'] if is_fr else ['en'], gpu=False)
        for f in files:
            if "pdf" in f.type:
                with pdfplumber.open(f) as pdf:
                    txt = " ".join([p.extract_text() or "" for p in pdf.pages])
            else:
                img = np.array(Image.open(f))
                txt = " ".join(reader.readtext(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), detail=0))
            st.session_state.brain_memory += f"\n[{f.name}]: {txt}"
        st.success("Knowledge Core Updated!")

# --- 4. CHAT INTERFACE ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command FreDèlAi..."):
    # Pattern Learning Logic
    if "=" in prompt and len(prompt.split("=")) == 2:
        k, v = prompt.split("=")
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast(f"Learned: {k} is {v}")

    # Process prompt with learned patterns
    display_p = prompt
    for k, v in st.session_state.patterns.items():
        if k in prompt.lower(): prompt = prompt.lower().replace(k, v)

    st.session_state.messages.append({"role": "user", "content": display_p})
    with st.chat_message("user"): st.markdown(display_p)

    with st.chat_message("assistant"):
        # IMAGE LOGIC
        if any(x in display_p.lower() for x in ["draw", "image", "paint"]):
            with st.spinner("🎨 Forcing Image Generation..."):
                res = call_hf_api(prompt, "stabilityai/sdxl-turbo")
                if res: st.image(res)
                else: st.error("Servers are truly jammed. Try 'draw a red ball' to test.")
        
        # VIDEO LOGIC
        elif "video" in display_p.lower():
            with st.status("🎥 Rendering (Hunyuan)...") as s:
                res = call_hf_api(prompt, "tencent/HunyuanVideo")
                if res:
                    st.video(res)
                    s.update(label="Complete!", state="complete")
                else:
                    s.update(label="Server Timeout", state="error")
        
        # TEXT LOGIC (GROQ)
        else:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            ctx = f"Context: {st.session_state.brain_memory[:2000]}"
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
