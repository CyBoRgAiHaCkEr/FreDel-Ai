import streamlit as st
import numpy as np, requests, time, json
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq

# --- 1. CONFIG & SYSTEM BRAIN ---
st.set_page_config(page_title="FreDèlAi Infinity", page_icon="♾️", layout="wide")

for key in ["brain_memory", "messages", "patterns"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else ("" if key == "brain_memory" else {})

# --- 2. THE INFINITY MEDIA ENGINES (NO QUEUES) ---
def generate_instant_video(prompt):
    """Bypasses HF using the 2026 decentralized Vheer/Pollinations bridge"""
    # Clean the prompt for URL safety
    clean_p = prompt.replace(" ", "%20")
    seed = np.random.randint(0, 999999)
    # This endpoint provides free, no-signup 5-second video clips
    video_url = f"https://video.pollinations.ai/prompt/{clean_p}?seed={seed}"
    return video_url

# --- 3. SIDEBAR: THE PERMANENT BRAIN PORT ---
with st.sidebar:
    st.title("🤖 FreDèlAi Infinity")
    st.subheader("💾 Brain Port")
    
    # Download Brain (Forever Storage)
    brain_data = {"mem": st.session_state.brain_memory, "pat": st.session_state.patterns}
    st.download_button("📥 Save Brain to PC", data=json.dumps(brain_data), file_name="fredel_infinity_brain.json")
    
    # Upload Brain (Restore Memory)
    up_brain = st.file_uploader("📤 Load Brain from PC", type="json")
    if up_brain and st.button("🔄 Restore Memory"):
        b = json.load(up_brain)
        st.session_state.brain_memory, st.session_state.patterns = b['mem'], b['pat']
        st.success("Memory Restored!")
        st.rerun()

    st.divider()
    files = st.file_uploader("Sync Knowledge", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("⚡ Process"):
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

# --- 4. CHAT INTERFACE ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command FreDèlAi..."):
    # Pattern Learning
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
        # INSTANT IMAGE
        if any(x in display_p.lower() for x in ["draw", "image", "paint"]):
            seed = np.random.randint(0, 99999)
            img_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ','%20')}?seed={seed}&nologo=true"
            st.image(img_url, caption="Infinity Vision Generated")
        
        # INSTANT VIDEO (NO HF BUSY ERRORS)
        elif "video" in display_p.lower():
            with st.spinner("🎥 Tapping into Decentralized Nodes..."):
                v_url = generate_instant_video(prompt)
                st.video(v_url)
                st.info("Video generated via Infinity Loop. No server limits.")
        
        # TEXT ENGINE (GROQ)
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
