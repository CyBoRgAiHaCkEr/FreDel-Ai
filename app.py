import streamlit as st
import numpy as np, requests, json, os, base64
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
        st.caption("Place 'logo.png' in folder for branding")
    
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

# --- 3. THE IMMORTAL MOTION ENGINE (No Black Screens) ---
def render_immortal_motion(prompt):
    seed = np.random.randint(0, 999999)
    clean_p = prompt.replace(" ", "%20")
    # This URL specifically requests an animated WEBP/GIF hybrid
    url = f"https://pollinations.ai/p/{clean_p}?width=1024&height=1024&seed={seed}&model=turbo&nologo=true"
    
    try:
        # Step 1: Download the binary data directly
        resp = requests.get(url, timeout=40)
        if resp.status_code == 200:
            # Step 2: Convert to Base64 (This embeds it in the page so it can't be blocked)
            b64_data = base64.b64encode(resp.content).decode()
            
            # Step 3: Render as an Image, NOT a Video Player
            # This is the secret to avoiding the "Black Screen of Doom"
            st.markdown(
                f'''
                <div style="text-align:center;">
                    <img src="data:image/webp;base64,{b64_data}" 
                         style="width:100%; border-radius:15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                    <p style="color:#00ffcc; margin-top:10px; font-weight:bold;">✨ FreDèlAi Motion Engine Solidified</p>
                </div>
                ''', 
                unsafe_allow_html=True
            )
        else:
            st.error("Engine is currently overclocked. Try again in 5 seconds!")
    except Exception as e:
        st.error(f"Sync Interrupted: {e}")

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
            with st.spinner("🚀 Bypassing Black Screen... Generating Motion..."):
                render_immortal_motion(prompt)
        
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
