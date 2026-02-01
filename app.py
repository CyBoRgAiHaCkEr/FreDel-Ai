import streamlit as st
import os, numpy as np, requests, time, json, base64
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq

# --- 1. CONFIG & STATE ---
st.set_page_config(page_title="FreDèlAi Infinity", layout="wide")

if "messages" not in st.session_state: st.session_state.messages = []
if "patterns" not in st.session_state: st.session_state.patterns = {}
if "brain_memory" not in st.session_state: 
    st.session_state.brain_memory = "Core: Delu, Mumbai-based French Educator."

# --- 2. SIDEBAR (LOGO, BRAIN PORT, OCR) ---
with st.sidebar:
    if os.path.exists("logo.jpg"): st.image("logo.jpg", width='stretch')
    elif os.path.exists("logo.png"): st.image("logo.png", width='stretch')
    
    st.divider()
    st.subheader("💾 Brain Control")
    brain_data = {"mem": st.session_state.brain_memory, "patterns": st.session_state.patterns}
    st.download_button("📥 Download Brain", data=json.dumps(brain_data), file_name="delu_brain.json")
    
    up_brain = st.file_uploader("📤 Upload Brain", type="json")
    if up_brain and st.button("🔄 Force Sync"):
        b = json.load(up_brain)
        st.session_state.brain_memory = b.get('mem', "")
        st.session_state.patterns = b.get('patterns', {})
        st.rerun()

    st.divider()
    st.subheader("🔍 OCR Engine")
    is_fr = st.toggle("French Mode", value=False)
    files = st.file_uploader("Sync Worksheets (PDF/IMG)", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("⚡ Run OCR"):
        with st.spinner("Reading knowledge..."):
            reader = easyocr.Reader(['en', 'fr'] if is_fr else ['en'], gpu=False)
            for f in files:
                if "pdf" in f.type:
                    with pdfplumber.open(f) as pdf:
                        txt = " ".join([p.extract_text() or "" for p in pdf.pages])
                else:
                    img = np.array(Image.open(f))
                    txt = " ".join(reader.readtext(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), detail=0))
                # Persistent storage for OCR text
                st.session_state.brain_memory += f"\n[FILE: {f.name}]: {txt}"
            st.success("Knowledge embedded in Brain!")

# --- 3. CHAT LOGIC ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Enter command or question..."):
    # COMMAND LOGIC: If you say "taii is [text]", it saves that shortcut
    if " is " in prompt.lower() and len(prompt.split()) < 25:
        key, val = prompt.lower().split(" is ", 1)
        st.session_state.patterns[key.strip()] = val.strip()
        st.toast(f"Pattern Set: {key}")

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        # BYPASS: If word is a shortcut (like 'taii'), print it directly
        cmd = prompt.lower().strip()
        if cmd in st.session_state.patterns:
            ans = st.session_state.patterns[cmd]
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
        else:
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                # We show the AI the patterns so it knows them too
                rules = "\n".join([f"Shortcut '{k}' means: {v}" for k, v in st.session_state.patterns.items()])
                
                sys_msg = (
                    f"You are FreDèlAi (Delu). Profile: {st.session_state.brain_memory}\n"
                    f"KNOWN SHORTCUTS:\n{rules}\n"
                    "If the user uses a shortcut word, repeat its meaning. Otherwise, answer as Delu."
                )
                
                r = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"system","content":sys_msg}] + st.session_state.messages[-8:]
                )
                ans = r.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except:
                st.error("API error. Please wait 60s.")
