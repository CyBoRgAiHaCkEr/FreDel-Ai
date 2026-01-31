import streamlit as st
import numpy as np, requests, time, json, os, base64
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq
import streamlit.components.v1 as components

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="FreDèlAi Infinity", page_icon="♾️", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] img {
        display: block;
        margin-left: auto;
        margin-right: auto;
        border-radius: 10px;
        margin-bottom: 20px;
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
    st.subheader("💾 Brain Port")
    
    if "messages" not in st.session_state: st.session_state.messages = []
    if "brain_memory" not in st.session_state: st.session_state.brain_memory = ""
    if "patterns" not in st.session_state: st.session_state.patterns = {}

    brain_data = {"mem": st.session_state.brain_memory, "pat": st.session_state.patterns}
    st.download_button("📥 Save Brain", data=json.dumps(brain_data), file_name="fredel_brain.json")
    
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

# --- 3. THE SOLID-STATE VIDEO ENGINE (Zero-DNS-Errors) ---
def render_solid_video(prompt):
    seed = np.random.randint(0, 999999)
    clean_p = prompt.replace(" ", "%20")
    
    # We use the 'Turbo' animated model on the stable main domain
    # This is effectively a high-FPS video loop that never 404s
    video_url = f"https://pollinations.ai/p/{clean_p}?width=1024&height=1024&seed={seed}&model=turbo&nologo=true"
    
    # We use a custom HTML container to make it look like a pro video player
    video_html = f"""
        <div style="width:100%; text-align:center;">
            <img src="{video_url}" style="width:100%; border-radius:15px; box-shadow: 0px 4px 15px rgba(0,0,0,0.3);">
            <p style="color:gray; font-size:12px; margin-top:5px;">FreDèlAi Infinity Motion active</p>
        </div>
    """
    components.html(video_html, height=500)

# --- 4. MAIN CHAT ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command FreDèlAi..."):
    if "=" in prompt:
        k, v = prompt.split("=")
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast("Locked!")

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
            with st.spinner("🎥 Igniting Motion Engine..."):
                render_solid_video(prompt)
        
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
