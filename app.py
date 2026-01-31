import streamlit as st
import numpy as np, requests, json, os, time, base64
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
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.title("🤖 FreDèlAi")
    
    # Initialize States
    if "messages" not in st.session_state: st.session_state.messages = []
    if "brain_memory" not in st.session_state: st.session_state.brain_memory = ""
    
    st.divider()
    # FRENCH MODE TOGGLE
    french_mode = st.toggle("🇫🇷 Mode Français", value=False)
    
    st.subheader("💾 Memory Command")
    # DOWNLOAD MEMORY
    mem_data = json.dumps({"mem": st.session_state.brain_memory, "chat": st.session_state.messages})
    st.download_button("📥 Download Brain", data=mem_data, file_name="fredel_brain.json")
    
    # LOAD MEMORY
    uploaded_brain = st.file_uploader("📤 Load Brain File", type="json")
    if uploaded_brain and st.button("🔄 Restore Memory"):
        data = json.load(uploaded_brain)
        st.session_state.brain_memory = data.get("mem", "")
        st.session_state.messages = data.get("chat", [])
        st.success("Brain Restored!")

    st.divider()
    # OCR FILE SYNC
    files = st.file_uploader("⚡ Sync Knowledge (PDF/IMG)", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("🔍 Run OCR Sync"):
        reader = easyocr.Reader(['en', 'fr']) # Supports both!
        for f in files:
            if "pdf" in f.type:
                with pdfplumber.open(f) as pdf:
                    txt = " ".join([p.extract_text() or "" for p in pdf.pages])
            else:
                img = np.array(Image.open(f))
                txt = " ".join(reader.readtext(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), detail=0))
            # Append and smart-trim to last 5000 chars to prevent API crashes
            st.session_state.brain_memory = (st.session_state.brain_memory + f"\n[{f.name}]: " + txt)[-5000:]
        st.success("OCR Sync Complete!")

# --- 3. MOTION ENGINE ---
def render_motion(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1024&height=1024&model=turbo&nologo=true"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            with open("temp_motion.webp", "wb") as f: f.write(resp.content)
            st.image("temp_motion.webp", caption="✨ FreDèlAi Motion")
    except: st.error("Visual Link Failed.")

# --- 4. MAIN CHAT ENGINE ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command FreDèlAi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        if any(x in prompt.lower() for x in ["draw", "image", "video", "motion"]):
            render_motion(prompt)
        else:
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                
                # SYSTEM PROMPT LOGIC
                sys_msg = "You are FreDèlAi. "
                if french_mode: sys_msg += "You MUST respond ONLY in French. "
                sys_msg += f"Context: {st.session_state.brain_memory[-2000:]}"
                
                # Use llama-3.1-8b-instant for higher rate limits
                r = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"system","content":sys_msg}] + st.session_state.messages[-6:]
                )
                ans = r.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except Exception as e:
                st.error("⚠️ Rate Limit! Try 'Download Brain', then 'Reset Tokens'.")
