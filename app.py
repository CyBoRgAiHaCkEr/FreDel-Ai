import streamlit as st
import os, numpy as np, requests, time, json, base64
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq
from gtts import gTTS

# --- 1. CONFIG & DESIGN ---
st.set_page_config(page_title="FreDèlAi Infinity", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] img { border-radius: 8px; border: 1px solid #00ffcc; margin-bottom: 10px; }
    .stChatMessage { border-radius: 15px; border-left: 4px solid #00ffcc; background-color: rgba(0, 255, 204, 0.05); }
    </style>
    """, unsafe_allow_html=True)

# Persistent Memory Keys
for key in ["brain_memory", "messages", "patterns"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else ("" if key == "brain_memory" else {})

# --- 2. HIGH-STABILITY IMAGE ENGINE ---
def get_safe_image(prompt):
    clean_p = prompt.replace(" ", "%20")
    # Triple-Retry Loop to bypass "Server Busy" errors
    for attempt in range(3):
        seed = int(time.time()) + np.random.randint(1000, 99999)
        url = f"https://pollinations.ai/p/{clean_p}?seed={seed}&width=1024&height=1024&nologo=true"
        
        try:
            # Masquerade as a browser to avoid bot-blocking
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            resp = requests.get(url, timeout=30, headers=headers)
            
            if resp.status_code == 200 and len(resp.content) > 10000:
                b64 = base64.b64encode(resp.content).decode()
                return f'''
                <div style="text-align:center;">
                    <img src="data:image/png;base64,{b64}" 
                         style="width:100%; border-radius:15px; border: 2px solid #00ffcc; 
                         box-shadow: 0 4px 20px rgba(0,255,204,0.5);">
                </div>
                '''
            time.sleep(1.5) # Short pause before retry
        except:
            continue
            
    return "⚠️ The Vision Core is currently overloaded. Please wait 10 seconds and try again."

# --- 3. SIDEBAR (LOGO, OCR & BRAIN PORT) ---
with st.sidebar:
    # Supports your rectangular logo.jpg
    if os.path.exists("logo.jpg"): st.image("logo.jpg", use_container_width=True)
    elif os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.title("🤖 FreDèlAi")

    st.divider()
    st.subheader("💾 Brain Port")
    brain_data = {"mem": st.session_state.brain_memory, "pat": st.session_state.patterns}
    st.download_button("📥 Export Brain", data=json.dumps(brain_data), file_name="fredel_brain.json")
    
    up_brain = st.file_uploader("📤 Load Brain", type="json")
    if up_brain and st.button("🔄 Sync Brain"):
        b = json.load(up_brain)
        st.session_state.brain_memory, st.session_state.patterns = b['mem'], b['pat']
        st.success("Memory Loaded!")
        st.rerun()

    st.divider()
    is_fr = st.toggle("French Mode", value=False)
    
    # OCR Section
    files = st.file_uploader("OCR: Knowledge Sync", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("⚡ Run OCR"):
        with st.spinner("🔍 Reading Files..."):
            reader = easyocr.Reader(['en', 'fr'] if is_fr else ['en'], gpu=False)
            for f in files:
                if "pdf" in f.type:
                    with pdfplumber.open(f) as pdf:
                        txt = " ".join([p.extract_text() or "" for p in pdf.pages])
                else:
                    img = np.array(Image.open(f))
                    txt = " ".join(reader.readtext(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), detail=0))
                st.session_state.brain_memory = (st.session_state.brain_memory + f"\n[{f.name}]: {txt}")[-5000:]
            st.success("Core Updated!")

# --- 4. CHAT ENGINE ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Command FreDèlAi..."):
    # Pattern Learning Logic
    if "=" in prompt and len(prompt.split("=")) == 2:
        k, v = prompt.split("=")
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast(f"Pattern Learned: {k.strip()}")

    display_p = prompt
    # Apply learned patterns
    for k, v in st.session_state.patterns.items():
        if k in prompt.lower(): prompt = prompt.lower().replace(k, v)

    st.session_state.messages.append({"role": "user", "content": display_p})
    with st.chat_message("user"): st.markdown(display_p)

    with st.chat_message("assistant"):
        # IMAGE GENERATION TRIGGER
        if any(x in display_p.lower() for x in ["draw", "image", "paint", "generate", "dessine"]):
            with st.spinner("🎨 Solidifying Vision..."):
                img_html = get_safe_image(prompt)
                st.markdown(img_html, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": img_html})
        
        # TEXT GENERATION (Groq)
        else:
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                sys_msg = f"You are FreDèlAi. Knowledge: {st.session_state.brain_memory[-1500:]}"
                if is_fr: sys_msg += ". RESPOND ONLY IN FRENCH."
                
                r = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"system","content":sys_msg}] + st.session_state.messages[-5:]
                )
                ans = r.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                
                # Voice Trigger
                if "speak" in display_p.lower() or "parle" in display_p.lower():
                    gTTS(text=ans[:300], lang='fr' if is_fr else 'en').save("v.mp3")
                    st.audio("v.mp3", autoplay=True)
            except:
                st.error("API Limit Reached. Please wait 60s.")
