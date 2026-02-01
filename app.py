import streamlit as st
import os, numpy as np, requests, time, json, base64
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq
from gtts import gTTS

# --- 1. CONFIG ---
st.set_page_config(page_title="FreDèlAi Infinity", page_icon="🤖", layout="wide")

# Persistent State
if "messages" not in st.session_state: st.session_state.messages = []
if "patterns" not in st.session_state: st.session_state.patterns = {}
if "brain_memory" not in st.session_state: 
    st.session_state.brain_memory = "Delu: Mumbai-based French educator. Expert in grammar patterns and board exams."

# --- 2. IMAGE ENGINE ---
def get_safe_image(prompt, manual_seed):
    clean_p = prompt.replace(" ", "%20")
    models = ["flux", "turbo", "any-dark"]
    for model in models:
        final_seed = manual_seed + np.random.randint(1, 1000)
        url = f"https://pollinations.ai/p/{clean_p}?model={model}&seed={final_seed}&nologo=true"
        try:
            resp = requests.get(url, timeout=25)
            if resp.status_code == 200 and len(resp.content) > 15000:
                b64 = base64.b64encode(resp.content).decode()
                return f'<img src="data:image/png;base64,{b64}" style="width:100%; border-radius:15px; border: 2px solid #00ffcc;">'
        except: continue
    return "⚠️ Clusters busy. Change Seed."

# --- 3. SIDEBAR ---
with st.sidebar:
    # Use 'width' for 2026 compatibility
    if os.path.exists("logo.jpg"): st.image("logo.jpg", width='stretch')
    elif os.path.exists("logo.png"): st.image("logo.png", width='stretch')
    else: st.title("🤖 FreDèlAi")

    st.divider()
    v_seed = st.number_input("Vision Seed", value=123, step=1)
    
    st.divider()
    st.subheader("💾 Brain Port")
    
    # Export logic - matching your JSON style
    brain_data = {"mem": st.session_state.brain_memory, "patterns": st.session_state.patterns}
    st.download_button("📥 Download Brain", data=json.dumps(brain_data), file_name="delu_brain.json")
    
    # Import logic - NOW MATCHES YOUR JSON KEY "patterns"
    up_brain = st.file_uploader("📤 Upload Brain", type="json")
    if up_brain and st.button("🔄 Sync Brain"):
        try:
            b = json.load(up_brain)
            st.session_state.brain_memory = b.get('mem', st.session_state.brain_memory)
            # This line now looks for 'patterns' instead of 'pat'
            st.session_state.patterns = b.get('patterns', {}) 
            st.success("Memory Restored!")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()
    is_fr = st.toggle("French Mode", value=False)
    files = st.file_uploader("OCR Sync", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("⚡ Run OCR"):
        reader = easyocr.Reader(['en', 'fr'] if is_fr else ['en'], gpu=False)
        for f in files:
            if "pdf" in f.type:
                with pdfplumber.open(f) as pdf:
                    txt = " ".join([p.extract_text() or "" for p in pdf.pages])
            else:
                img = np.array(Image.open(f))
                txt = " ".join(reader.readtext(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), detail=0))
            st.session_state.brain_memory = (st.session_state.brain_memory + f"\n[{f.name}]: {txt}")[-4000:]
        st.success("Knowledge Updated!")

# --- 4. CHAT ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Command FreDèlAi..."):
    # Pattern Logic
    display_p = prompt
    for k, v in st.session_state.patterns.items():
        if k in prompt.lower(): prompt = prompt.lower().replace(k, v)

    st.session_state.messages.append({"role": "user", "content": display_p})
    with st.chat_message("user"): st.markdown(display_p)

    with st.chat_message("assistant"):
        if any(x in display_p.lower() for x in ["draw", "image", "paint"]):
            img_html = get_safe_image(prompt, v_seed)
            st.markdown(img_html, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": img_html})
        else:
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                sys_msg = f"You are FreDèlAi (Delu). Bio: {st.session_state.brain_memory}. Always use full sentences and teaching patterns."
                r = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"system","content":sys_msg}] + st.session_state.messages[-5:]
                )
                ans = r.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                
                if "speak" in display_p.lower():
                    gTTS(text=ans[:300], lang='fr' if is_fr else 'en').save("v.mp3")
                    st.audio("v.mp3", autoplay=True)
            except: st.error("API Limit.")
