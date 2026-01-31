import streamlit as st
import numpy as np, requests, json, os, time
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq

# --- 1. CONFIG ---
st.set_page_config(page_title="FreDèlAi Infinity", page_icon="♾️", layout="wide")

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("🤖 FreDèlAi")
    st.caption("2026 Stable Build")
    
    if "messages" not in st.session_state: st.session_state.messages = []
    if "brain_memory" not in st.session_state: st.session_state.brain_memory = ""

    # EMERGENCY RESET: If you hit a rate limit, click this.
    if st.button("🗑️ Reset Tokens (Clear History)"):
        st.session_state.messages = []
        st.session_state.brain_memory = ""
        st.rerun()

# --- 3. THE "DISK-FLUSH" MOTION ENGINE ---
def render_motion_physical(prompt):
    seed = np.random.randint(0, 999999)
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1024&height=1024&seed={seed}&model=turbo&nologo=true"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # We save locally to ensure NO BROKEN ICONS
            with open("temp_motion.webp", "wb") as f:
                f.write(response.content)
            st.image("temp_motion.webp", caption="✨ FreDèlAi Motion")
    except Exception as e:
        st.error(f"Visual Error: {e}")

# --- 4. MAIN CHAT ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command FreDèlAi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        if any(x in prompt.lower() for x in ["draw", "image", "video", "motion"]):
            with st.spinner("🚀 Generating..."):
                render_motion_physical(prompt)
        else:
            try:
                # IMPORTANT: Use your NEW key in Streamlit Secrets!
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                
                # THE CIRCUIT BREAKER:
                # 1. Only send the last 5 messages to save tokens.
                # 2. Cap the extra knowledge to 1000 characters.
                safe_history = st.session_state.messages[-5:]
                safe_brain = st.session_state.brain_memory[-1000:]
                
                # Swapping to llama-3.1-8b-instant (Higher limits than the 70b)
                r = client.chat.completions.create(
                    model="llama-3.1-8b-instant", 
                    messages=[{"role":"system","content":f"You are FreDèlAi. Knowledge: {safe_brain}"}] + safe_history
                )
                ans = r.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except Exception as e:
                if "429" in str(e) or "413" in str(e):
                    st.error("🚨 Context Overload! Click 'Reset Tokens' in the sidebar and try again.")
                else:
                    st.error(f"Error: {e}")
