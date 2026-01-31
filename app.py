import streamlit as st
import os, numpy as np, requests, time, json, base64
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq
from gtts import gTTS

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="FreDèlAi Infinity", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] img { border-radius: 10px; border: 2px solid #00ffcc; margin-bottom: 15px; }
    .stChatMessage { border-radius: 15px; border-left: 5px solid #00ffcc; background-color: rgba(0, 255, 204, 0.03); }
    [data-testid="stSidebar"] { background-color: #0e1117; }
    </style>
    """, unsafe_allow_html=True)

# Initialize Session States
for key in ["brain_memory", "messages", "patterns"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else ("" if key == "brain_memory" else {})

# --- 2. THE TITANIUM VISION ENGINE ---
def get_safe_image(prompt):
    clean_p = prompt.replace(" ", "%20")
    # Try 4 times across different model endpoints
    for attempt in range(4):
        seed = int(time.time()) + np.random.randint(1000, 99999)
        # Alternate endpoints to bypass specific server loads
        url = f"https://pollinations.ai/p/{clean_p}?seed={seed}&width=1024&height=1024&nologo=true" if attempt % 2 == 0 else \
              f"https://image.pollinations.ai/prompt/{clean_p}?seed={seed}&nologo=true"
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            resp = requests.get(url, timeout=40, headers=headers)
            
            if resp.status_code == 200 and len(resp.content) > 8000:
                b64 = base64.b64encode(resp.content).decode()
                return f'''
                <div style="text-align:center;">
                    <img src="data:image/png;base64,{b64}" 
                         style="width:100%; border-radius:15px; border: 2px solid #00ffcc; 
                         box-shadow: 0 4px 25px rgba(0,255,204,0.6);">
                </div>
                '''
            time.sleep(2.5) # Wait for server breather
        except:
            continue
            
    return "⚠️ **Vision Core Saturated.** The server is under high load. Please wait 30s and try a shorter prompt."

# --- 3. SIDEBAR: LOGO, OCR & BRAIN ---
with st.sidebar:
    # Handle Rectangular JPG Logo
    if os.path.exists("logo.jpg"): st.image("logo.jpg", use_container_width=True)
    elif os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.title("🤖 FreDèlAi")

    st.divider()
    st.subheader("💾 Memory & Patterns")
    # Export / Import
    brain_data = {"mem": st.session_state.brain_memory, "pat": st.session_state.patterns}
    st.download_button("📥 Save Brain", data=json.dumps(brain_data), file_name="fredel_brain.json")
    
    up_brain = st.file_uploader("📤 Load Brain", type="json")
    if up_brain and st.button("🔄 Restore Memory"):
        b = json.load(up_brain)
        st.session_state.brain_memory, st.session_state.patterns = b['mem'], b['pat']
        st.success("Core Synchronized!")
        st.rerun()

    st.divider()
    is_fr = st.toggle("French Mode", value=False)
    
    # OCR Engine
    files = st.file_uploader("⚡ Sync Knowledge (PDF/IMG)", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("🔍 Scan & Remember"):
        with st.spinner("Reading into Memory..."):
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

# --- 4. THE CHAT ENGINE ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Command FreDèlAi Infinity..."):
    # Pattern Learning Logic
    if "=" in prompt and len(prompt.split("=")) == 2:
        k, v = prompt.split("=")
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast(f"New Pattern: {k.strip()}")

    display_p = prompt
    # Apply Patterns
    for k, v in st.session_state.patterns.items():
        if k in prompt.lower(): prompt = prompt.lower().replace(k, v)

    st.session_state.messages.append({"role": "user", "content": display_p})
    with st.chat_message("user"): st.markdown(display_p)

    with st.chat_message("assistant"):
        # IMAGE LOGIC
        if any(x in display_p.lower() for x in ["draw", "image", "paint", "generate"]):
            with st.spinner("🎨 Forging Visual Reality..."):
                img_html = get_safe_image(prompt)
                st.markdown(img_html, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": img_html})
        
        # TEXT LOGIC (Groq)
        else:
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                sys_msg = f"You are FreDèlAi. Core Memory: {st.session_state.brain_memory[-1200:]}"
                if is_fr: sys_msg += ". RESPOND ONLY IN FRENCH."
                
                r = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"system","content":sys_msg}] + st.session_state.messages[-6:]
                )
                ans = r.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                
                # Audio TTS
                if "speak" in display_p.lower() or "parle" in display_p.lower():
                    gTTS(text=ans[:300], lang='fr' if is_fr else 'en').save("v.mp3")
                    st.audio("v.mp3", autoplay=True)
            except:
                st.error("The API is thinking too hard. Please wait 60 seconds.")
