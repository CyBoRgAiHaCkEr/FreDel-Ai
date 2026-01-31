import streamlit as st
import numpy as np, requests, json, os, io, base64
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="FreDèlAi Infinity", page_icon="♾️", layout="wide")

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
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.title("🤖 FreDèlAi")
    
    st.divider()
    if "messages" not in st.session_state: st.session_state.messages = []
    if "brain_memory" not in st.session_state: st.session_state.brain_memory = ""
    if "patterns" not in st.session_state: st.session_state.patterns = {}

    st.subheader("💾 Brain Port")
    st.download_button("📥 Save Brain", data=json.dumps({"mem": st.session_state.brain_memory, "pat": st.session_state.patterns}), file_name="fredel_brain.json")
    
    up_brain = st.file_uploader("📤 Load Brain", type="json")
    if up_brain and st.button("🔄 Restore"):
        b = json.load(up_brain)
        st.session_state.brain_memory, st.session_state.patterns = b['mem'], b['pat']
        st.rerun()

    st.divider()
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

# --- 3. THE LOCAL BUFFER ENGINE ---
def render_buffered_video(prompt):
    seed = np.random.randint(0, 999999)
    # Using the high-speed motion-webp format which browsers handle better than MP4
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1024&height=1024&seed={seed}&model=turbo&nologo=true"
    
    try:
        # Step 1: Python fetches the video data behind the scenes
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # Step 2: Convert binary data to a Base64 string
            video_b64 = base64.b64encode(response.content).decode()
            
            # Step 3: Use a native HTML container to play it from local memory
            st.markdown(
                f'''
                <div style="text-align:center;">
                    <img src="data:image/webp;base64,{video_b64}" style="width:100%; border-radius:15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                    <p style="color:#00ffcc; margin-top:10px;">✨ FreDèlAi Motion Active (Buffered)</p>
                </div>
                ''', 
                unsafe_allow_html=True
            )
        else:
            st.error("Server is a bit slow. Hit enter again!")
    except Exception as e:
        st.error(f"Buffer Error: {e}")

# --- 4. MAIN CHAT ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command FreDèlAi..."):
    if "=" in prompt:
        k, v = prompt.split("=")
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast("Pattern Locked!")

    display_p = prompt
    for k, v in st.session_state.patterns.items():
        if k in prompt.lower(): prompt = prompt.lower().replace(k, v)

    st.session_state.messages.append({"role": "user", "content": display_p})
    with st.chat_message("user"): st.markdown(display_p)

    with st.chat_message("assistant"):
        if any(x in display_p.lower() for x in ["draw", "image", "paint"]):
            seed = np.random.randint(0, 99999)
            st.image(f"https://pollinations.ai/p/{prompt.replace(' ','%20')}?width=1024&height=1024&seed={seed}&nologo=true")
        
        elif "video" in display_p.lower():
            with st.spinner("🚀 Buffering Motion Feed..."):
                render_buffered_video(prompt)
        
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
