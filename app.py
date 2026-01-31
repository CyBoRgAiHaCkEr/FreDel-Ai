import streamlit as st
import numpy as np, requests, time, json, os
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="FreDèlAi Infinity", page_icon="♾️", layout="wide")

# This CSS ensures your mom's rectangular logo stays centered and looks pro
st.markdown("""
    <style>
    [data-testid="stSidebar"] img {
        display: block; margin-left: auto; margin-right: auto;
        border-radius: 10px; margin-bottom: 20px;
    }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR & LOGO BRIDGE ---
with st.sidebar:
    # If you put 'logo.png' in the folder, it appears here instantly
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.title("🤖 FreDèlAi")
        st.caption("Place 'logo.png' in folder to activate branding")
    
    st.divider()
    if "messages" not in st.session_state: st.session_state.messages = []
    if "brain_memory" not in st.session_state: st.session_state.brain_memory = ""
    if "patterns" not in st.session_state: st.session_state.patterns = {}

    st.subheader("💾 Brain Port")
    # Save the brain (patterns and memory) to a file
    st.download_button("📥 Save Brain", data=json.dumps({"mem": st.session_state.brain_memory, "pat": st.session_state.patterns}), file_name="fredel_brain.json")
    
    # Upload a previous brain file
    up_brain = st.file_uploader("📤 Load Brain", type="json")
    if up_brain and st.button("🔄 Restore"):
        b = json.load(up_brain)
        st.session_state.brain_memory, st.session_state.patterns = b['mem'], b['pat']
        st.rerun()

    st.divider()
    # Knowledge Sync (OCR for PDFs and Images)
    files = st.file_uploader("Sync Knowledge", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("⚡ Sync Core"):
        reader = easyocr.Reader(['en'], gpu=False)
        for f in files:
            if "pdf" in f.type:
                with pdfplumber.open(f) as pdf:
                    txt = " ".join([p.extract_text() or "" for p in pdf.pages])
            else:
                img = np.array(Image.open(f))
                txt = " ".join(reader.readtext(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), detail=0))
            st.session_state.brain_memory += f"\n[{f.name}]: {txt}"
        st.success("Brain Updated!")

# --- 3. MAIN CHAT INTERFACE ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command FreDèlAi..."):
    # Pattern Learning (e.g., "red ball = shiny sports car")
    if "=" in prompt:
        k, v = prompt.split("=")
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast("Pattern Locked!")

    display_p = prompt
    # Swap out words based on learned patterns
    for k, v in st.session_state.patterns.items():
        if k in prompt.lower(): prompt = prompt.lower().replace(k, v)

    st.session_state.messages.append({"role": "user", "content": display_p})
    with st.chat_message("user"): st.markdown(display_p)

    with st.chat_message("assistant"):
        # COMMAND: Draw/Image
        if any(x in display_p.lower() for x in ["draw", "image", "paint"]):
            seed = np.random.randint(0, 99999)
            st.image(f"https://pollinations.ai/p/{prompt.replace(' ','%20')}?width=1024&height=1024&seed={seed}&nologo=true")
        
        # COMMAND: Video (The Final Working Fix)
        elif "video" in display_p.lower():
            with st.spinner("🎥 Igniting Native Motion..."):
                seed = np.random.randint(0, 999999)
                # The 'turbo' model creates a motion-webp that st.video can handle perfectly
                video_url = f"https://pollinations.ai/p/{prompt.replace(' ','%20')}?width=1024&height=1024&seed={seed}&model=turbo&nologo=true"
                st.video(video_url, format="video/mp4", loop=True, autoplay=True, muted=True)
                st.caption("✨ FreDèlAi Infinity Motion Active")
        
        # COMMAND: Text (The Brain)
        else:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            ctx = f"Brain Memory: {st.session_state.brain_memory[:2000]}"
            r = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role":"system","content":f"You are FreDèlAi. {ctx}"}] + st.session_state.messages
            )
            ans = r.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
