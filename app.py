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

# --- 3. THE INFALLIBLE VHEER VIDEO ENGINE (No 404s) ---
def render_video_vheer(prompt):
    clean_p = prompt.replace(" ", "%20")
    # Vheer 2026 Decentralized API - Instant and Free
    vheer_url = f"https://vheer.pollinations.ai/generate/{clean_p}"
    
    try:
        # We request the video clip (standard 5-second 2026 loop)
        response = requests.get(vheer_url, timeout=90)
        
        if response.status_code == 200:
            b64_video = base64.b64encode(response.content).decode()
            video_tag = f"""
                <video width="100%" autoplay loop muted controls style="border-radius:10px;">
                    <source src="data:video/mp4;base64,{b64_video}" type="video/mp4">
                </video>
            """
            components.html(video_tag, height=450)
        else:
            # If Vheer fails, we use a smart fallback to a high-quality GIF
            st.warning("Video Engine busy. Showing high-quality preview...")
            gif_url = f"https://gen.pollinations.ai/prompt/{clean_p}?model=anim"
            st.image(gif_url)
    except Exception as e:
        st.error(f"Media Error: {e}")

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
            st.image(f"https://gen.pollinations.ai/prompt/{prompt.replace(' ','%20')}?seed={seed}&nologo=true")
        
        elif "video" in display_p.lower():
            with st.spinner("🎥 Vheer Node Processing..."):
                render_video_vheer(prompt)
        
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
