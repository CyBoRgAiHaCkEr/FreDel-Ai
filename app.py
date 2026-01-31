import streamlit as st
import numpy as np, requests, json, os, base64
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="FreDèlAi Infinity", page_icon="♾️", layout="wide")

# --- 2. THE IMAGE PROXY (Bypasses Broken Icons) ---
def get_safe_image_html(prompt):
    seed = np.random.randint(0, 999999)
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1024&height=1024&seed={seed}&nologo=true"
    try:
        # Python downloads the image data behind the scenes
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            # Convert binary data to Base64
            b64_str = base64.b64encode(response.content).decode()
            # Return raw HTML with the image embedded
            return f'<img src="data:image/png;base64,{b64_str}" style="width:100%; border-radius:15px; border: 2px solid #00ffcc;">'
    except:
        return "⚠️ Sync Failed. Try again!"
    return "⚠️ Could not reach core."

# --- 3. SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.jpg"): st.image("logo.jpg", use_container_width=True)
    elif os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.title("🤖 FreDèlAi")
    
    if "messages" not in st.session_state: st.session_state.messages = []
    if "brain_memory" not in st.session_state: st.session_state.brain_memory = ""
    
    french_mode = st.toggle("🇫🇷 Mode Français", value=False)
    
    if st.button("🗑️ Reset Tokens"):
        st.session_state.messages = []
        st.session_state.brain_memory = ""
        st.rerun()

    st.divider()
    # OCR & FILE LOADING
    files = st.file_uploader("Sync Knowledge", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("🔍 Run Sync"):
        reader = easyocr.Reader(['en', 'fr'])
        for f in files:
            if "pdf" in f.type:
                with pdfplumber.open(f) as pdf:
                    txt = " ".join([p.extract_text() or "" for p in pdf.pages])
            else:
                img = np.array(Image.open(f))
                txt = " ".join(reader.readtext(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), detail=0))
            st.session_state.brain_memory = (st.session_state.brain_memory + "\n" + txt)[-3000:]
        st.success("Core Updated")

# --- 4. MAIN CHAT ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Command FreDèlAi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        if any(x in prompt.lower() for x in ["draw", "image", "paint", "generate"]):
            with st.spinner("🎨 Creating..."):
                img_html = get_safe_image_html(prompt)
                st.markdown(img_html, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": img_html})
        else:
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                sys_msg = f"You are FreDèlAi. Context: {st.session_state.brain_memory[-1000:]}."
                if french_mode: sys_msg += " RESPOND ONLY IN FRENCH."
                
                r = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"system","content":sys_msg}] + st.session_state.messages[-5:]
                )
                ans = r.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except:
                st.error("Rate Limit! Reset tokens in sidebar.")
