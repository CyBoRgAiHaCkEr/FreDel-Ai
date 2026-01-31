import streamlit as st
import numpy as np, requests, json, os
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="FreDèlAi Infinity", page_icon="♾️", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] img { display: block; margin: auto; border-radius: 10px; margin-bottom: 20px; }
    .stChatMessage { border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR (Memory, OCR, & French Mode) ---
with st.sidebar:
    # Use logo.jpg if it exists
    if os.path.exists("logo.jpg"): st.image("logo.jpg", use_container_width=True)
    elif os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.title("🤖 FreDèlAi")
    
    if "messages" not in st.session_state: st.session_state.messages = []
    if "brain_memory" not in st.session_state: st.session_state.brain_memory = ""
    
    st.divider()
    french_mode = st.toggle("🇫🇷 Mode Français", value=False)
    
    st.subheader("💾 Memory Command")
    mem_data = json.dumps({"mem": st.session_state.brain_memory, "chat": st.session_state.messages})
    st.download_button("📥 Download Brain", data=mem_data, file_name="fredel_brain.json")
    
    uploaded_brain = st.file_uploader("📤 Load Brain File", type="json")
    if uploaded_brain and st.button("🔄 Restore Memory"):
        data = json.load(uploaded_brain)
        st.session_state.brain_memory = data.get("mem", "")
        st.session_state.messages = data.get("chat", [])
        st.rerun()

    st.divider()
    files = st.file_uploader("⚡ Sync Knowledge", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("🔍 Run OCR Sync"):
        reader = easyocr.Reader(['en', 'fr'])
        for f in files:
            if "pdf" in f.type:
                with pdfplumber.open(f) as pdf:
                    txt = " ".join([p.extract_text() or "" for p in pdf.pages])
            else:
                img = np.array(Image.open(f))
                txt = " ".join(reader.readtext(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), detail=0))
            st.session_state.brain_memory = (st.session_state.brain_memory + f"\n[{f.name}]: " + txt)[-5000:]
        st.success("Core Synced!")

# --- 3. MAIN CHAT ENGINE ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command FreDèlAi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        # NORMAL IMAGE GENERATION (FAST)
        if any(x in prompt.lower() for x in ["draw", "image", "paint", "generate"]):
            with st.spinner("🎨 Creating..."):
                seed = np.random.randint(0, 999999)
                url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1024&height=1024&seed={seed}&nologo=true"
                st.image(url, caption="✨ FreDèlAi Vision")
        
        else:
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                sys_msg = "You are FreDèlAi. "
                if french_mode: sys_msg += "Respond ONLY in French. "
                sys_msg += f"Context: {st.session_state.brain_memory[-2000:]}"
                
                # Using the stable instant model
                r = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"system","content":sys_msg}] + st.session_state.messages[-6:]
                )
                ans = r.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except Exception as e:
                st.error("Rate Limit reached. Please wait a moment.")
