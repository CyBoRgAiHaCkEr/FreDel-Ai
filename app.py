import streamlit as st
import os, numpy as np, requests, time, json
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq
from gtts import gTTS

# --- 1. CONFIG & SYSTEM BRAIN ---
st.set_page_config(page_title="FreDèlAi 2026", page_icon="🤖", layout="wide")

# Persistent memory keys
for key in ["brain_memory", "messages", "patterns"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else ("" if key == "brain_memory" else {})

# --- 2. THE RESILIENT API ENGINES ---
def call_hf_api(prompt, model_id):
    """Used specifically for Video (Hugging Face)"""
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}", "X-Wait-For-Model": "true"}
    try:
        resp = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=100)
        if resp.status_code == 200 and len(resp.content) > 1000:
            return resp.content
    except:
        return None
    return None

# --- 3. SIDEBAR: THE BRAIN PORT (UPLOAD/DOWNLOAD) ---
with st.sidebar:
    st.title("🤖 FreDèlAi Control")
    
    # --- BRAIN EXPORT ---
    st.subheader("💾 Export Brain")
    brain_data = {"mem": st.session_state.brain_memory, "pat": st.session_state.patterns}
    st.download_button("📥 Download Brain (.json)", data=json.dumps(brain_data), file_name="fredel_brain.json")
    
    # --- BRAIN IMPORT ---
    up_brain = st.file_uploader("📤 Load Brain", type="json")
    if up_brain and st.button("🔄 Sync"):
        b = json.load(up_brain)
        st.session_state.brain_memory, st.session_state.patterns = b['mem'], b['pat']
        st.success("Brain Loaded!")
        st.rerun()

    st.divider()
    # OCR Section
    is_fr = st.checkbox("French Mode", value=True)
    files = st.file_uploader("Sync Files", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("⚡ Sync Knowledge"):
        reader = easyocr.Reader(['fr', 'en'] if is_fr else ['en'], gpu=False)
        for f in files:
            if "pdf" in f.type:
                with pdfplumber.open(f) as pdf:
                    txt = " ".join([p.extract_text() or "" for p in pdf.pages])
            else:
                img = np.array(Image.open(f))
                txt = " ".join(reader.readtext(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), detail=0))
            st.session_state.brain_memory += f"\n[{f.name}]: {txt}"
        st.success("Core Updated!")

# --- 4. CHAT INTERFACE ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command FreDèlAi..."):
    # Pattern Learning Logic (e.g. apple=red_ball)
    if "=" in prompt and len(prompt.split("=")) == 2:
        k, v = prompt.split("=")
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast(f"Pattern Learned!")

    display_p = prompt
    # Apply patterns to the prompt
    for k, v in st.session_state.patterns.items():
        if k in prompt.lower(): prompt = prompt.lower().replace(k, v)

    st.session_state.messages.append({"role": "user", "content": display_p})
    with st.chat_message("user"): st.markdown(display_p)

    with st.chat_message("assistant"):
        # IMAGE: Bypasses HF Queues using Pollinations
        if any(x in display_p.lower() for x in ["draw", "image", "paint"]):
            with st.spinner("🎨 Generating Instant Image..."):
                seed = np.random.randint(0, 99999)
                # Clean prompt for URL
                clean_p = prompt.replace(" ", "%20")
                img_url = f"https://image.pollinations.ai/prompt/{clean_p}?seed={seed}&nologo=true&width=1024&height=1024"
                st.image(img_url, caption=f"FreDèlAi Vision: {display_p}")
        
        # VIDEO: Zeroscope (Requires HF Token)
        elif "video" in display_p.lower():
            with st.status("🎥 Rendering Video...") as s:
                res = call_hf_api(prompt, "vdo/zeroscope_v2_576w")
                if res:
                    st.video(res)
                    s.update(label="Complete!", state="complete")
                else:
                    s.update(label="HF Server Busy (Video Only)", state="error")
        
        # TEXT: Groq Llama 3.3
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
            if "speak" in display_p.lower():
                gTTS(text=ans[:300], lang='fr' if is_fr else 'en').save("v.mp3")
                st.audio("v.mp3", autoplay=True)
