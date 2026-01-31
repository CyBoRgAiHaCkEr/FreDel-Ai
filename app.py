import streamlit as st
import os, numpy as np, requests, time, json, io
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq
from gtts import gTTS

# --- 1. CONFIG & SYSTEM BRAIN ---
st.set_page_config(page_title="FreDèlAi Infinity", page_icon="🤖", layout="wide")

# Persistent memory keys
for key in ["brain_memory", "messages", "patterns"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else ("" if key == "brain_memory" else {})

# --- 2. THE IMAGE ENGINE (Physical Cache Fix) ---
def render_safe_image(prompt):
    seed = np.random.randint(0, 99999)
    clean_p = prompt.replace(" ", "%20")
    url = f"https://image.pollinations.ai/prompt/{clean_p}?seed={seed}&nologo=true&width=1024&height=1024"
    try:
        resp = requests.get(url, timeout=25)
        if resp.status_code == 200:
            # Physically save to disk to bypass browser security blocks
            with open("vision_cache.png", "wb") as f:
                f.write(resp.content)
            st.image("vision_cache.png", caption=f"FreDèlAi Vision: {prompt}")
            return True
    except:
        st.error("Connection to Core timed out.")
    return False

# --- 3. SIDEBAR: THE CONTROL CENTER ---
with st.sidebar:
    # Handle Rectangular JPG Logo
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", use_container_width=True)
    elif os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.title("🤖 FreDèlAi")

    st.divider()
    # BRAIN PORT (Up/Download)
    st.subheader("💾 Brain Port")
    brain_data = {"mem": st.session_state.brain_memory, "pat": st.session_state.patterns}
    st.download_button("📥 Download Brain", data=json.dumps(brain_data), file_name="fredel_brain.json")
    
    up_brain = st.file_uploader("📤 Load Brain", type="json")
    if up_brain and st.button("🔄 Sync Brain"):
        b = json.load(up_brain)
        st.session_state.brain_memory, st.session_state.patterns = b['mem'], b['pat']
        st.success("Brain Restored!")
        st.rerun()

    st.divider()
    # OCR & SYNC
    is_fr = st.toggle("French Mode", value=True)
    files = st.file_uploader("Sync Files", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("⚡ Sync Knowledge"):
        with st.spinner("🔍 Reading..."):
            reader = easyocr.Reader(['fr', 'en'] if is_fr else ['en'], gpu=False)
            for f in files:
                if "pdf" in f.type:
                    with pdfplumber.open(f) as pdf:
                        txt = " ".join([p.extract_text() or "" for p in pdf.pages])
                else:
                    img = np.array(Image.open(f))
                    txt = " ".join(reader.readtext(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), detail=0))
                # Append to brain memory (limit last 5000 chars for API safety)
                st.session_state.brain_memory = (st.session_state.brain_memory + f"\n[{f.name}]: {txt}")[-5000:]
            st.success("Core Updated!")

# --- 4. CHAT INTERFACE ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command FreDèlAi..."):
    # Pattern Learning Logic (e.g. apple=red_ball)
    if "=" in prompt and len(prompt.split("=")) == 2:
        k, v = prompt.split("=")
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast(f"Pattern Learned: {k.strip()}")

    display_p = prompt
    # Apply patterns
    for k, v in st.session_state.patterns.items():
        if k in prompt.lower(): prompt = prompt.lower().replace(k, v)

    st.session_state.messages.append({"role": "user", "content": display_p})
    with st.chat_message("user"): st.markdown(display_p)

    with st.chat_message("assistant"):
        # IMAGE GENERATION
        if any(x in display_p.lower() for x in ["draw", "image", "paint"]):
            with st.spinner("🎨 Solidifying Vision..."):
                render_safe_image(prompt)
        
        # TEXT GENERATION (Groq)
        else:
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                sys_msg = f"You are FreDèlAi. Knowledge: {st.session_state.brain_memory[-2000:]}"
                if is_fr: sys_msg += ". Respond ONLY in French."
                
                # Using 8b model to avoid rate limit crashes (413/429)
                r = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"system","content":sys_msg}] + st.session_state.messages[-5:]
                )
                ans = r.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                
                # TTS Audio
                if "speak" in display_p.lower() or "parle" in display_p.lower():
                    gTTS(text=ans[:300], lang='fr' if is_fr else 'en').save("v.mp3")
                    st.audio("v.mp3", autoplay=True)
            except Exception as e:
                st.error("API Limit reached. Wait 60s or clear history.")
