import streamlit as st
import os, numpy as np
import pdfplumber, easyocr
from PIL import Image
from groq import Groq
from gtts import gTTS

# --- 1. SYSTEM BRANDING & CONFIG ---
st.set_page_config(page_title="FreDèlAi Mainframe", page_icon="🇫🇷", layout="wide")

# --- 2. SESSION & MEMORY ---
if "brain_memory" not in st.session_state: st.session_state.brain_memory = ""
if "messages" not in st.session_state: st.session_state.messages = []
if "patterns" not in st.session_state: st.session_state.patterns = {}

# --- 3. DYNAMIC ENGINES (NO HINDI) ---
@st.cache_resource
def get_ocr(is_french):
    # 'fr' includes all French accents; 'en' is the base.
    langs = ['fr', 'en'] if is_french else ['en']
    return easyocr.Reader(langs, gpu=False)

# --- 4. SIDEBAR CONTROL ---
with st.sidebar:
    st.title("🤖 FreDèlAi")
    st.caption("v6.0 | English-French Specialist")
    
    # Simple Toggle
    is_fr = st.checkbox("Enable French OCR (Accents Support)", value=True)
    reader = get_ocr(is_fr)

    st.divider()
    st.subheader("🧠 Learned Shortcuts")
    if st.session_state.patterns:
        for k, v in st.session_state.patterns.items():
            st.caption(f"**{k}** = {v}")
    else:
        st.info("Example: `taii = type as it is`")

    # File Upload
    files = st.file_uploader("Upload Image/PDF", type=["pdf","png","jpg","jpeg"], accept_multiple_files=True)
    if st.button("Update Core ⚡"):
        with st.spinner("Analyzing..."):
            for f in files:
                if "pdf" in f.type:
                    with pdfplumber.open(f) as pdf:
                        txt = " ".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                else:
                    # Clean extraction (no bounding box junk)
                    txt = " ".join(reader.readtext(np.array(Image.open(f)), detail=0))
                st.session_state.brain_memory += f"\n[{f.name}]: {txt}"
            st.success("Memory Updated.")

    if st.button("🗑️ Wipe Memory"):
        st.session_state.brain_memory = ""; st.session_state.patterns = {}; st.rerun()

# --- 5. CHAT TERMINAL ---
st.write(f"### Bienvenue. I am **FreDèlAi**.")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command FreDèlAi..."):
    # Pattern Learning Logic
    if "=" in prompt and len(prompt.split("=")) == 2:
        k, v = prompt.split("=")
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast("Meaning Integrated.")

    # Pattern Swap
    processed_p = prompt.lower()
    for k, v in st.session_state.patterns.items():
        if k in processed_p: processed_p = processed_p.replace(k, v)

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        # Fetch Key from GitHub Secrets/Streamlit Cloud
        api_key = st.secrets.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
        client = Groq(api_key=api_key)
        
        ctx = f"Brain: {st.session_state.brain_memory[:4000]}"
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": f"You are FreDèlAi, a bilingual AI. Context: {ctx}"}] + st.session_state.messages
        )
        ans = response.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})

        # Voice Trigger
        if any(w in prompt.lower() for w in ["speak", "say", "talk"]):
            # Intelligent language switching for voice
            voice_lang = 'fr' if any(fr_word in ans.lower() for fr_word in ["le", "la", "est", "je", "est"]) else 'en'
            try:
                tts = gTTS(text=ans[:500], lang=voice_lang)
                tts.save("speech.mp3")
                st.audio("speech.mp3", autoplay=True)
            except:
                st.error("Voice synthesis currently unavailable.")
