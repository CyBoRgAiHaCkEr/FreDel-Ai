import streamlit as st
import os, numpy as np, requests, time, json, base64
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq
from gtts import gTTS

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="FreDèlAi Infinity", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] img { border-radius: 10px; border: 2px solid #00ffcc; margin-bottom: 15px; }
    .stChatMessage { border-radius: 15px; border-left: 5px solid #00ffcc; background-color: rgba(0, 255, 204, 0.05); }
    </style>
    """, unsafe_allow_html=True)

# Initialize States
for key in ["brain_memory", "messages", "patterns"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else ("" if key == "brain_memory" else {})

# --- 2. VISION ENGINE (Dual-Engine + Seed Bypass) ---
def get_safe_image(prompt, manual_seed):
    clean_p = prompt.replace(" ", "%20")
    models = ["flux", "turbo", "any-dark", "unity"]
    
    for model in models:
        final_seed = manual_seed + np.random.randint(1, 1000)
        url = f"https://pollinations.ai/p/{clean_p}?model={model}&seed={final_seed}&width=1024&height=1024&nologo=true"
        
        try:
            headers = {'User-Agent': f'FreDelAi-2026-{final_seed}'}
            resp = requests.get(url, timeout=35, headers=headers)
            
            # Validation: Block small placeholder/error images
            if resp.status_code == 200 and len(resp.content) > 15000:
                b64 = base64.b64encode(resp.content).decode()
                return f'''
                <div style="text-align:center;">
                    <img src="data:image/png;base64,{b64}" 
                         style="width:100%; border-radius:15px; border: 2px solid #00ffcc; 
                         box-shadow: 0 4px 30px rgba(0,255,204,0.6);">
                </div>
                '''
            time.sleep(1)
        except:
            continue
            
    return "⚠️ **All Clusters Saturated.** Change the 'Vision Seed' in the sidebar and try again!"

# --- 3. SIDEBAR (LOGO, BRAIN PORT, OCR) ---
with st.sidebar:
    # 🖼️ THE LOGO
    if os.path.exists("logo.jpg"): st.image("logo.jpg", use_container_width=True)
    elif os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.title("🤖 FreDèlAi")

    st.divider()

    # 🛡️ THE SEED BYPASS
    st.subheader("🛡️ Vision Controls")
    v_seed = st.number_input("Vision Seed (Bypass Limit)", value=42, step=1)
    
    st.divider()

    # 💾 BRAIN PORT (Download/Upload Brain)
    st.subheader("💾 Brain Port")
    brain_data = {"mem": st.session_state.brain_memory, "pat": st.session_state.patterns}
    st.download_button("📥 Download Brain (.json)", 
                       data=json.dumps(brain_data), 
                       file_name="fredel_brain.json",
                       help="Export learned patterns and OCR memory.")
    
    up_brain = st.file_uploader("📤 Upload Brain (.json)", type="json")
    if up_brain and st.button("🔄 Sync Brain"):
        b = json.load(up_brain)
        st.session_state.brain_memory, st.session_state.patterns = b['mem'], b['pat']
        st.success("Memory Synchronized!")
        st.rerun()

    st.divider()

    # ⚡ OCR & KNOWLEDGE
    st.subheader("🔍 OCR Engine")
    is_fr = st.toggle("French Mode", value=False)
    files = st.file_uploader("Upload Knowledge (PDF/IMG)", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("⚡ Sync Knowledge"):
        with st.spinner("Processing Files..."):
            reader = easyocr.Reader(['en', 'fr'] if is_fr else ['en'], gpu=False)
            for f in files:
                if "pdf" in f.type:
                    with pdfplumber.open(f) as pdf:
                        txt = " ".join([p.extract_text() or "" for p in pdf.pages])
                else:
                    img = np.array(Image.open(f))
                    txt = " ".join(reader.readtext(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), detail=0))
                st.session_state.brain_memory = (st.session_state.brain_memory + f"\n[{f.name}]: {txt}")[-5000:]
            st.success("Brain Updated!")

# --- 4. CHAT INTERFACE ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Command FreDèlAi Infinity..."):
    # Pattern Logic
    if "=" in prompt and len(prompt.split("=")) == 2:
        k, v = prompt.split("=")
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast(f"Pattern Learned: {k.strip()}")

    display_p = prompt
    for k, v in st.session_state.patterns.items():
        if k in prompt.lower(): prompt = prompt.lower().replace(k, v)

    st.session_state.messages.append({"role": "user", "content": display_p})
    with st.chat_message("user"): st.markdown(display_p)

    with st.chat_message("assistant"):
        if any(x in display_p.lower() for x in ["draw", "image", "paint", "generate"]):
            with st.spinner("🎨 Forging Visuals..."):
                img_html = get_safe_image(prompt, v_seed)
                st.markdown(img_html, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": img_html})
        else:
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                sys_msg = f"You are FreDèlAi. Brain Context: {st.session_state.brain_memory[-1500:]}"
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
                st.error("Groq API Busy. Wait 60s.")
