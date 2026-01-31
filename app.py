import streamlit as st
import os, numpy as np, requests, time, json, base64
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq
from gtts import gTTS

# --- 1. SYSTEM CONFIG ---
st.set_page_config(page_title="FreDèlAi Infinity", page_icon="🤖", layout="wide")

# Persistent State Management
for key in ["brain_memory", "messages", "patterns"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else ("" if key == "brain_memory" else {})

# --- 2. THE VISION ENGINE (Multi-Model Failover) ---
def get_safe_image(prompt, manual_seed):
    clean_p = prompt.replace(" ", "%20")
    # 2026 Strategy: Cycle through 4 distinct clusters
    endpoints = [
        f"https://pollinations.ai/p/{clean_p}?model=flux&seed={manual_seed}&nologo=true",
        f"https://gen.pollinations.ai/image/{clean_p}?model=turbo&seed={manual_seed}&nologo=true",
        f"https://image.pollinations.ai/prompt/{clean_p}?seed={manual_seed + 1}&width=1024&height=1024",
        f"https://pollinations.ai/p/{clean_p}?model=unity&seed={manual_seed}&nologo=true"
    ]
    
    for url in endpoints:
        try:
            # Mask the request as a fresh browser session
            headers = {'User-Agent': f'Mozilla/5.0 (AI-Agent-{manual_seed})'}
            resp = requests.get(url, timeout=30, headers=headers)
            
            # Validation: Block small "Saturated" error images (usually < 15KB)
            if resp.status_code == 200 and len(resp.content) > 15000:
                b64 = base64.b64encode(resp.content).decode()
                return f'''
                <div style="text-align:center;">
                    <img src="data:image/png;base64,{b64}" 
                         style="width:100%; border-radius:15px; border: 2px solid #00ffcc; 
                         box-shadow: 0 4px 30px rgba(0,255,204,0.6);">
                </div>
                '''
            time.sleep(1) # Breath between cluster hops
        except:
            continue
            
    return "⚠️ **All Clusters Saturated.** The network is heavily congested. Change the **Vision Seed** in the sidebar to refresh your fingerprint!"

# --- 3. SIDEBAR (LOGO, BRAIN PORT, OCR) ---
with st.sidebar:
    # 🖼️ LOGO RECOVERY
    if os.path.exists("logo.jpg"): st.image("logo.jpg", use_container_width=True)
    elif os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.title("🤖 FreDèlAi")

    st.divider()
    
    # 🛡️ BYPASS CONTROLS
    st.subheader("🛡️ Bypass Settings")
    v_seed = st.number_input("Vision Seed (Change if blocked)", value=np.random.randint(1, 10000), step=1)
    
    st.divider()

    # 💾 BRAIN PORT (DOWNLOAD/UPLOAD)
    st.subheader("💾 Brain Port")
    brain_data = {"mem": st.session_state.brain_memory, "pat": st.session_state.patterns}
    st.download_button("📥 Download Brain (.json)", 
                       data=json.dumps(brain_data), 
                       file_name="fredel_brain.json")
    
    up_brain = st.file_uploader("📤 Upload Brain (.json)", type="json")
    if up_brain and st.button("🔄 Sync Brain"):
        b = json.load(up_brain)
        st.session_state.brain_memory, st.session_state.patterns = b['mem'], b['pat']
        st.success("Memory Restored!")
        st.rerun()

    st.divider()

    # ⚡ OCR & KNOWLEDGE
    st.subheader("🔍 Knowledge Sync")
    is_fr = st.toggle("French Mode", value=False)
    files = st.file_uploader("Sync PDF/Images", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("⚡ Run OCR"):
        reader = easyocr.Reader(['en', 'fr'] if is_fr else ['en'], gpu=False)
        for f in files:
            if "pdf" in f.type:
                with pdfplumber.open(f) as pdf:
                    txt = " ".join([p.extract_text() or "" for p in pdf.pages])
            else:
                img = np.array(Image.open(f))
                txt = " ".join(reader.readtext(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), detail=0))
            st.session_state.brain_memory = (st.session_state.brain_memory + f"\n[{f.name}]: {txt}")[-5000:]
        st.success("Core Brain Updated!")

# --- 4. CHAT LOGIC ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Command FreDèlAi Infinity..."):
    # Pattern Logic
    if "=" in prompt and len(prompt.split("=")) == 2:
        k, v = prompt.split("=")
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast(f"Learned: {k.strip()}")

    display_p = prompt
    for k, v in st.session_state.patterns.items():
        if k in prompt.lower(): prompt = prompt.lower().replace(k, v)

    st.session_state.messages.append({"role": "user", "content": display_p})
    with st.chat_message("user"): st.markdown(display_p)

    with st.chat_message("assistant"):
        if any(x in display_p.lower() for x in ["draw", "image", "paint", "generate"]):
            with st.spinner("🎨 Forcing through the clusters..."):
                img_html = get_safe_image(prompt, v_seed)
                st.markdown(img_html, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": img_html})
        else:
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                sys_msg = f"You are FreDèlAi. Brain: {st.session_state.brain_memory[-1200:]}"
                if is_fr: sys_msg += ". RESPOND ONLY IN FRENCH."
                
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
            except:
                st.error("API Limit. Wait 60s.")
