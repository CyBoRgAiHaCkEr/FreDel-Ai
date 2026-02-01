import streamlit as st
import os, numpy as np, requests, time, json, base64
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq
from gtts import gTTS

# --- 1. CONFIG ---
st.set_page_config(page_title="FreDèlAi Infinity", page_icon="🤖", layout="wide")

if "messages" not in st.session_state: st.session_state.messages = []
if "patterns" not in st.session_state: st.session_state.patterns = {}
if "brain_memory" not in st.session_state: 
    st.session_state.brain_memory = "NAME: Delu (FreDèlAi). LOCATION: Mumbai. ROLE: French Systems-Driven Educator."

# --- 2. IMAGE ENGINE ---
def get_safe_image(prompt, manual_seed):
    clean_p = prompt.replace(" ", "%20")
    url = f"https://pollinations.ai/p/{clean_p}?model=flux&seed={manual_seed}&nologo=true"
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 15000:
            b64 = base64.b64encode(resp.content).decode()
            return f'<img src="data:image/png;base64,{b64}" style="width:100%; border-radius:15px; border: 2px solid #00ffcc;">'
    except: pass
    return "⚠️ Server busy. Try a new seed."

# --- 3. SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.jpg"): st.image("logo.jpg", width='stretch')
    elif os.path.exists("logo.png"): st.image("logo.png", width='stretch')
    
    st.divider()
    v_seed = st.number_input("Vision Seed", value=42, step=1)
    
    st.subheader("💾 Brain Port")
    brain_data = {"mem": st.session_state.brain_memory, "patterns": st.session_state.patterns}
    st.download_button("📥 Download Brain", data=json.dumps(brain_data), file_name="delu_brain.json")
    
    up_brain = st.file_uploader("📤 Upload Brain", type="json")
    if up_brain and st.button("🔄 Sync Brain"):
        b = json.load(up_brain)
        st.session_state.brain_memory = b.get('mem', st.session_state.brain_memory)
        st.session_state.patterns = b.get('patterns', {})
        st.success("Memory Restored!")

# --- 4. CHAT LOGIC ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Talk to FreDèlAi..."):
    # SMART MEMORY: If you say "X is Y", it remembers it forever in the brain
    if " is " in prompt.lower() and len(prompt.split()) < 10:
        st.session_state.brain_memory += f" | Fact: {prompt}"
        st.toast(f"Memorized: {prompt}")

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        if any(x in prompt.lower() for x in ["draw", "image", "paint"]):
            img_html = get_safe_image(prompt, v_seed)
            st.markdown(img_html, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": img_html})
        else:
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                # We feed the AI the entire accumulated memory so it knows who 'Taii' is.
                sys_msg = (
                    f"You are FreDèlAi (Delu). Your background: {st.session_state.brain_memory}. "
                    "You have a human-like memory. If the user mentioned a name or fact earlier, use it. "
                    "Always answer fully and helpfully in the style of a structured educator."
                )
                
                r = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"system","content":sys_msg}] + st.session_state.messages[-10:]
                )
                ans = r.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except:
                st.error("Connection lost. Please wait.")
