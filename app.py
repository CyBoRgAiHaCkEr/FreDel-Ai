import streamlit as st
import os, numpy as np, requests, time
import pdfplumber, easyocr
from PIL import Image
from groq import Groq
from gtts import gTTS

# --- 1. SYSTEM BRANDING & CONFIG ---
st.set_page_config(page_title="FreDèlAi Mainframe", page_icon="🤖", layout="wide")

# --- 2. SESSION & MEMORY INITIALIZATION ---
if "brain_memory" not in st.session_state: st.session_state.brain_memory = ""
if "messages" not in st.session_state: st.session_state.messages = []
if "patterns" not in st.session_state: st.session_state.patterns = {}

# --- 3. ENGINES (OCR & MULTIMEDIA) ---
@st.cache_resource
def get_ocr(is_french):
    langs = ['fr', 'en'] if is_french else ['en']
    return easyocr.Reader(langs, gpu=False)

def call_hf_api(prompt, model_url):
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    response = requests.post(model_url, headers=headers, json={"inputs": prompt})
    return response.content if response.status_code == 200 else None

# --- 4. SIDEBAR CONTROL CENTER ---
with st.sidebar:
    st.title("🤖 FreDèlAi Controls")
    
    # OCR Toggle
    is_fr = st.checkbox("Enable French Mode", value=True)
    reader = get_ocr(is_fr)

    st.divider()
    
    # File Processor
    files = st.file_uploader("Upload Docs/Images", type=["pdf","png","jpg","jpeg"], accept_multiple_files=True)
    if st.button("Update Neural Core ⚡"):
        with st.spinner("Absorbing data..."):
            for f in files:
                if "pdf" in f.type:
                    with pdfplumber.open(f) as pdf:
                        txt = " ".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                else:
                    txt = " ".join(reader.readtext(np.array(Image.open(f)), detail=0))
                st.session_state.brain_memory += f"\n[{f.name}]: {txt}"
            st.success("Memory Updated!")

    st.divider()
    st.subheader("🧹 Memory Management")
    
    if st.button("🗑️ Wipe Files Only"):
        st.session_state.brain_memory = ""
        st.success("Files erased. Meanings safe!")
        time.sleep(1)
        st.rerun()

    if st.button("🧠 Forget Meanings"):
        st.session_state.patterns = {}
        st.success("All shortcuts reset!")
        time.sleep(1)
        st.rerun()

# --- 5. CHAT MAINFRAME ---
st.title("FreDèlAi Neural Terminal")

# Display Chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command FreDèlAi..."):
    # Shortcut Learning (e.g., taii = type as it is)
    if "=" in prompt and len(prompt.split("=")) == 2:
        k, v = prompt.split("=")
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast(f"Pattern '{k.strip()}' Learned!")

    # Apply Shortcuts
    display_prompt = prompt
    for k, v in st.session_state.patterns.items():
        if k in prompt.lower():
            prompt = prompt.lower().replace(k, v)

    st.session_state.messages.append({"role": "user", "content": display_prompt})
    with st.chat_message("user"): st.markdown(display_prompt)

    with st.chat_message("assistant"):
        # 1. Image Generation Check
        if any(x in display_prompt.lower() for x in ["draw", "generate image", "paint"]):
            with st.spinner("🎨 Creating artwork..."):
                img_data = call_hf_api(prompt, "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0")
                if img_data: st.image(img_data, caption="FreDèlAi Generated Image")
        
        # 2. Video Generation Check
        elif "video" in display_prompt.lower():
            with st.spinner("🎥 Rendering video (takes 30-60s)..."):
                vid_data = call_hf_api(prompt, "https://api-inference.huggingface.co/models/damo-vilab/modelscope-damo-text-to-video-generation")
                if vid_data: st.video(vid_data)

        # 3. Text/Knowledge Logic (Groq)
        else:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            ctx = f"Current Brain Memory: {st.session_state.brain_memory[:3000]}"
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": f"You are FreDèlAi. Context: {ctx}"}] + st.session_state.messages
            )
            ans = resp.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})

            # Voice Sync
            if "speak" in display_prompt.lower():
                voice_lang = 'fr' if any(w in ans.lower()[:50] for w in ["le", "la", "est", "je"]) else 'en'
                gTTS(text=ans[:500], lang=voice_lang).save("v.mp3")
                st.audio("v.mp3", autoplay=True)
