import streamlit as st
import os, numpy as np, requests, time, json
import pdfplumber, easyocr
from PIL import Image
from groq import Groq
from gtts import gTTS

# --- 1. SYSTEM BRANDING & CONFIG ---
st.set_page_config(page_title="FreDèlAi Mainframe", page_icon="🤖", layout="wide")

# --- 2. SESSION & MEMORY INITIALIZATION ---
if "brain_memory" not in st.session_state: st.session_state.brain_memory = ""
if "messages" not in st.session_state: st.session_state.messages = []
if "patterns" not in st.session_state: st.session_state.patterns = {}

# --- 3. ENGINES (OCR & MULTIMEDIA) ---
@st.cache_resource
def get_ocr(is_french):
    langs = ['fr', 'en'] if is_french else ['en']
    return easyocr.Reader(langs, gpu=False)

def call_hf_api(prompt, model_url):
    headers = {
        "Authorization": f"Bearer {st.secrets['HF_TOKEN']}",
        "X-Wait-For-Model": "true"
    }
    try:
        response = requests.post(model_url, headers=headers, json={"inputs": prompt}, timeout=120)
        return response.content if response.status_code == 200 else None
    except:
        return None

# --- 4. SIDEBAR CONTROL CENTER ---
with st.sidebar:
    st.title("🤖 FreDèlAi Controls")
    
    # Brain Export/Import (THE BRAIN PORT)
    st.subheader("💾 Brain Port")
    brain_data = json.dumps({
        "memory": st.session_state.brain_memory,
        "patterns": st.session_state.patterns
    })
    st.download_button("📥 Download Brain", data=brain_data, file_name="fredel_brain.json")
    
    uploaded_brain = st.file_uploader("📤 Upload Brain", type="json")
    if uploaded_brain and st.button("🔄 Sync Brain"):
        data = json.load(uploaded_brain)
        st.session_state.brain_memory = data.get("memory", "")
        st.session_state.patterns = data.get("patterns", {})
        st.success("Brain Restored!")
        st.rerun()

    st.divider()
    
    # File Processor
    is_fr = st.checkbox("Enable French OCR", value=True)
    files = st.file_uploader("Upload Docs/Images", type=["pdf","png","jpg","jpeg"], accept_multiple_files=True)
    if st.button("Update Neural Core ⚡"):
        reader = get_ocr(is_fr)
        with st.spinner("Absorbing data..."):
            for f in files:
                if "pdf" in f.type:
                    with pdfplumber.open(f) as pdf:
                        txt = " ".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                else:
                    txt = " ".join(reader.readtext(np.array(Image.open(f)), detail=0, paragraph=True))
                st.session_state.brain_memory += f"\n[{f.name}]: {txt}"
            st.success("Memory Updated!")

    st.divider()
    st.subheader("🧹 Maintenance")
    if st.button("🗑️ Wipe Files Only"):
        st.session_state.brain_memory = ""
        st.rerun()
    if st.button("🧠 Forget Meanings"):
        st.session_state.patterns = {}
        st.rerun()

# --- 5. CHAT MAINFRAME ---
st.title("FreDèlAi Neural Terminal")

# Display Chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command FreDèlAi..."):
    # Pattern Learning
    if "=" in prompt and len(prompt.split("=")) == 2:
        k, v = prompt.split("=")
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast("Pattern Learned!")

    # Apply Patterns
    display_prompt = prompt
    for k, v in st.session_state.patterns.items():
        if k in prompt.lower(): prompt = prompt.lower().replace(k, v)

    st.session_state.messages.append({"role": "user", "content": display_prompt})
    with st.chat_message("user"): st.markdown(display_prompt)

    with st.chat_message("assistant"):
        # MULTIMEDIA OVERRIDE
        if any(x in display_prompt.lower() for x in ["draw", "image of", "paint"]):
            with st.spinner("🎨 Painting..."):
                res = call_hf_api(prompt, "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0")
                if res: st.image(res)
        
        elif "video" in display_prompt.lower():
            with st.status("🎥 Rendering video...") as s:
                res = call_hf_api(prompt, "https://api-inference.huggingface.co/models/ali-vilab/modelscope-damo-text-to-video-generation")
                if res: st.video(res)
                s.update(label="Complete!", state="complete")

        else:
            # GROQ TEXT ENGINE
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            ctx = f"System Memory: {st.session_state.brain_memory[:2000]}"
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": f"You are FreDèlAi. {ctx}"}] + st.session_state.messages
            )
            ans = resp.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})

            if "speak" in display_prompt.lower():
                gTTS(text=ans[:300], lang='fr' if is_fr else 'en').save("v.mp3")
                st.audio("v.mp3", autoplay=True)
