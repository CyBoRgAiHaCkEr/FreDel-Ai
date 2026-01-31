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
    .stChatMessage { border-radius: 15px; border-left: 4px solid #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# Persistent Memory Keys
for key in ["brain_memory", "messages", "patterns"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else ("" if key == "brain_memory" else {})

# --- 2. SYSTEM FUNCTIONS ---
def get_safe_image(prompt):
    # Unique seed based on time ensures no rate-limit duplicates
    seed = int(time.time()) + np.random.randint(1000, 9999)
    clean_p = prompt.replace(" ", "%20")
    url = f"https://pollinations.ai/p/{clean_p}?seed={seed}&width=1024&height=1024&nologo=true"
    try:
        resp = requests.get(url, timeout=35)
        if resp.status_code == 200 and len(resp.content) > 5000:
            b64 = base64.b64encode(resp.content).decode()
            return f'<img src="data:image/png;base64,{b64}" style="width:100%; border-radius:15px; border: 2px solid #00ffcc; box-shadow: 0 4px 20px rgba(0,255,204,0.4);">'
    except:
        return "⚠️ Vision Core Link Failed."
    return "⚠️ Generation failed or server busy."

# --- 3. SIDEBAR (LOGO & BRAIN) ---
with st.sidebar:
    # Support for your rectangular JPG logo
    if os.path.exists("logo.jpg"): st.image("logo.jpg", use_container_width=True)
    elif os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.title("🤖 FreDèlAi")

    st.divider()
    st.subheader("💾 Brain Port")
    # Export
    brain_data = {"mem": st.session_state.brain_memory, "pat": st.session_state.patterns}
    st.download_button("📥 Download Brain", data=json.dumps(brain_data), file_name="fredel_brain.json")
    
    # Import
    up_brain = st.file_uploader("📤 Load Brain", type="json")
    if up_brain and st.button("🔄 Sync Brain"):
        b = json.load(up_brain)
        st.session_state.brain_memory, st.session_state.patterns = b['mem'], b['pat']
        st.success("Memory Restored!")
        st.rerun()

    st.divider()
    is_fr = st.toggle("French Mode", value=False)
    
    # OCR Section
    files = st.file_uploader("OCR: Sync Knowledge", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("⚡ Run OCR Sync"):
        reader = easyocr.Reader(['en', 'fr'] if is_fr else ['en'], gpu=False)
        for f in files:
            if "pdf" in f.type:
                with pdfplumber.open(f) as pdf:
                    txt = " ".join([p.extract_text() or "" for p in pdf.pages])
            else:
                img = np.array(Image.open(f))
                txt = " ".join(reader.readtext(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), detail=0))
            st.session_state.brain_memory = (st.session_state.brain_memory + f"\n[{f.name}]: {txt}")[-5000:]
        st.success("Knowledge Synchronized!")

# --- 4. CHAT INTERFACE ---
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
        # IMAGE GENERATION
        if any(x in display_p.lower() for x in ["draw", "image", "paint", "generate"]):
            with st.spinner("🎨 Generating Vision..."):
                img_html = get_safe_image(prompt)
                st.markdown(img_html, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": img_html})
        
        # TEXT GENERATION (Groq)
        else:
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                sys_msg = f"You are FreDèlAi. Knowledge Context: {st.session_state.brain_memory[-1500:]}"
                if is_fr: sys_msg += ". RESPOND ONLY IN FRENCH."
                
                r = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"system","content":sys_msg}] + st.session_state.messages[-5:]
                )
                ans = r.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                
                # TTS Voice Trigger
                if "speak" in display_p.lower() or "parle" in display_p.lower():
                    gTTS(text=ans[:300], lang='fr' if is_fr else 'en').save("v.mp3")
                    st.audio("v.mp3", autoplay=True)
            except:
                st.error("API Limit Reached. Wait 60s or clear history.")
