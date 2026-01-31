import streamlit as st
import os, numpy as np, requests, time, json
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq
from gtts import gTTS

# --- 1. CONFIG ---
st.set_page_config(page_title="FreDèlAi 2026", page_icon="🤖", layout="wide")

# --- 2. SESSION STATE ---
for key in ["brain_memory", "messages", "patterns"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else ("" if key == "brain_memory" else {})

# --- 3. THE RESILIENT API ENGINE ---
def call_hf_api(prompt, model_id):
    # 2026 Direct Inference Endpoint
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {
        "Authorization": f"Bearer {st.secrets['HF_TOKEN']}",
        "X-Wait-For-Model": "true",
        "X-Use-Cache": "false"
    }
    # Increased retry count with short sleeps
    for i in range(4):
        try:
            resp = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=120)
            if resp.status_code == 200 and len(resp.content) > 1000:
                return resp.content
            # If server is loading (503), wait 8 seconds
            if resp.status_code == 503:
                st.toast(f"🌀 Model waking up... retry {i+1}/4")
                time.sleep(8)
            else:
                time.sleep(2)
        except:
            continue
    return None

# --- 4. SIDEBAR: BRAIN PORT & OCR ---
with st.sidebar:
    st.title("🤖 FreDèlAi Control")
    
    st.subheader("💾 Brain Port")
    brain_data = json.dumps({"mem": st.session_state.brain_memory, "pat": st.session_state.patterns})
    st.download_button("📥 Save Brain", data=brain_data, file_name="fredel_brain.json")
    
    up_brain = st.file_uploader("📤 Load Brain", type="json")
    if up_brain and st.button("🔄 Sync"):
        b = json.load(up_brain)
        st.session_state.brain_memory, st.session_state.patterns = b['mem'], b['pat']
        st.rerun()

    st.divider()
    is_fr = st.checkbox("French Mode", value=True)
    files = st.file_uploader("Neural Core Upload", type=["pdf","png","jpg","jpeg"], accept_multiple_files=True)
    if st.button("⚡ Sync Knowledge"):
        reader = easyocr.Reader(['fr', 'en'] if is_fr else ['en'], gpu=False)
        for f in files:
            if "pdf" in f.type:
                with pdfplumber.open(f) as pdf:
                    txt = " ".join([p.extract_text() or "" for p in pdf.pages])
            else:
                img = np.array(Image.open(f))
                gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                txt = " ".join(reader.readtext(gray, detail=0, paragraph=True))
            st.session_state.brain_memory += f"\n[{f.name}]: {txt}"
        st.success("Knowledge Ingested!")

# --- 5. CHAT TERMINAL ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command FreDèlAi..."):
    # Pattern Logic (taii=... etc)
    if "=" in prompt and len(prompt.split("=")) == 2:
        k, v = prompt.split("=")
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast("Learned!")

    display_p = prompt
    for k, v in st.session_state.patterns.items():
        if k in prompt.lower(): prompt = prompt.lower().replace(k, v)

    st.session_state.messages.append({"role": "user", "content": display_p})
    with st.chat_message("user"): st.markdown(display_p)

    with st.chat_message("assistant"):
        # IMAGE LOGIC
        if any(x in display_p.lower() for x in ["draw", "image", "paint"]):
            with st.spinner("🎨 Generating Art..."):
                # SD-1.5 is used as the most stable fallback in 2026
                res = call_hf_api(prompt, "runwayml/stable-diffusion-v1-5")
                if res: st.image(res)
                else: st.error("Image Server overloaded. Try again in 30s.")
        
        # VIDEO LOGIC
        elif "video" in display_p.lower():
            with st.status("🎥 Rendering Video...", expanded=True) as s:
                # Zeroscope is the fastest free video model for dancing/motion
                res = call_hf_api(prompt, "vdo/zeroscope_v2_576w")
                if res:
                    st.video(res)
                    s.update(label="Complete!", state="complete")
                else:
                    s.update(label="Timeout. Server Busy.", state="error")
        
        # TEXT LOGIC
        else:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            ctx = f"System Memory: {st.session_state.brain_memory[:2500]}"
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
