import streamlit as st
import os, numpy as np, requests, time, json, base64
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq
from gtts import gTTS

# --- 1. SETTINGS & BRANDING ---
st.set_page_config(page_title="FreDèlAi Infinity", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] img { border-radius: 10px; border: 2px solid #00ffcc; margin-bottom: 15px; }
    .stChatMessage { border-radius: 15px; border-left: 5px solid #00ffcc; background-color: rgba(0, 255, 204, 0.05); }
    </style>
    """, unsafe_allow_html=True)

# Persistent State
for key in ["brain_memory", "messages", "patterns"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else ("" if key == "brain_memory" else {})

# --- 2. UNSTOPPABLE VISION ENGINE (Dual-Source Failover) ---
def get_safe_image(prompt):
    clean_p = prompt.replace(" ", "%20")
    # We will try 5 times, cycling through different server clusters
    for attempt in range(5):
        seed = int(time.time() * 1000) + np.random.randint(100, 9999)
        
        # Cycle through different API providers to find a free slot
        if attempt < 2:
            url = f"https://pollinations.ai/p/{clean_p}?seed={seed}&width=1024&height=1024&nologo=true"
        elif attempt < 4:
            url = f"https://image.pollinations.ai/prompt/{clean_p}?seed={seed}&width=768&height=768&nologo=true"
        else:
            # Emergency Backup Endpoint (Flux-Specific)
            url = f"https://pollinations.ai/p/{clean_p}?seed={seed}&model=flux&nologo=true"
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, timeout=35, headers=headers)
            
            # Check if we got a real image and not an "Overload" error page
            if resp.status_code == 200 and len(resp.content) > 12000:
                b64 = base64.b64encode(resp.content).decode()
                return f'''
                <div style="text-align:center;">
                    <img src="data:image/png;base64,{b64}" 
                         style="width:100%; border-radius:15px; border: 2px solid #00ffcc; 
                         box-shadow: 0 4px 30px rgba(0,255,204,0.6);">
                </div>
                '''
            time.sleep(2) # Breath before retry
        except:
            continue
            
    return "⚠️ **Global Traffic Alert.** All image clusters are currently full. Try a simpler prompt or wait 60s."

# --- 3. SIDEBAR (LOGO, OCR & BRAIN PORT) ---
with st.sidebar:
    if os.path.exists("logo.jpg"): st.image("logo.jpg", use_container_width=True)
    elif os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.title("🤖 FreDèlAi")

    st.divider()
    st.subheader("💾 Brain Port")
    brain_data = {"mem": st.session_state.brain_memory, "pat": st.session_state.patterns}
    st.download_button("📥 Save Brain", data=json.dumps(brain_data), file_name="fredel_brain.json")
    
    up_brain = st.file_uploader("📤 Load Brain", type="json")
    if up_brain and st.button("🔄 Sync Memory"):
        b = json.load(up_brain)
        st.session_state.brain_memory, st.session_state.patterns = b['mem'], b['pat']
        st.rerun()

    st.divider()
    is_fr = st.toggle("French Mode", value=False)
    files = st.file_uploader("OCR Knowledge Sync", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("⚡ Run Sync"):
        reader = easyocr.Reader(['en', 'fr'] if is_fr else ['en'], gpu=False)
        for f in files:
            if "pdf" in f.type:
                with pdfplumber.open(f) as pdf:
                    txt = " ".join([p.extract_text() or "" for p in pdf.pages])
            else:
                img = np.array(Image.open(f))
                txt = " ".join(reader.readtext(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), detail=0))
            st.session_state.brain_memory = (st.session_state.brain_memory + f"\n[{f.name}]: {txt}")[-4000:]
        st.success("Brain Updated!")

# --- 4. MAIN CHAT ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Command FreDèlAi..."):
    # Learning Pattern
    if "=" in prompt and len(prompt.split("=")) == 2:
        k, v = prompt.split("=")
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast(f"Pattern: {k.strip()}")

    display_p = prompt
    for k, v in st.session_state.patterns.items():
        if k in prompt.lower(): prompt = prompt.lower().replace(k, v)

    st.session_state.messages.append({"role": "user", "content": display_p})
    with st.chat_message("user"): st.markdown(display_p)

    with st.chat_message("assistant"):
        if any(x in display_p.lower() for x in ["draw", "image", "paint", "generate"]):
            with st.spinner("🎨 Trying all AI clusters..."):
                img_html = get_safe_image(prompt)
                st.markdown(img_html, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": img_html})
        else:
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                sys_msg = f"You are FreDèlAi. Context: {st.session_state.brain_memory[-1200:]}"
                if is_fr: sys_msg += ". RESPOND ONLY IN FRENCH."
                
                r = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"system","content":sys_msg}] + st.session_state.messages[-5:]
                )
                ans = r.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                
                if "speak" in display_p.lower() or "parle" in display_p.lower():
                    gTTS(text=ans[:300], lang='fr' if is_fr else 'en').save("v.mp3")
                    st.audio("v.mp3", autoplay=True)
            except:
                st.error("API Limit. Please wait 60s.")
