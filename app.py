import streamlit as st
import sqlite3
import base64
import os
from groq import Groq

# --- 1. CORE CONFIG ---
st.set_page_config(page_title="FreDèlAi", layout="wide")

MAVERICK = "groq/compound" 
DB_PATH = "permanent_brain.db"

# --- 2. THE SQLITE DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS patterns 
                 (keyword TEXT PRIMARY KEY, definition TEXT)''')
    conn.commit()
    conn.close()

def load_mem():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT keyword, definition FROM patterns")
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def save_pattern(k, v):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO patterns (keyword, definition) VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()

init_db()
if "patterns" not in st.session_state:
    st.session_state.patterns = load_mem()
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. VISION UTILS ---
def encode_img(file):
    return base64.b64encode(file.read()).decode('utf-8')

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("fredel-ai.streamlit.app")
    st.metric("Patterns in Memory", len(st.session_state.patterns))
    if st.button("Refresh"):
        st.session_state.patterns = load_mem()
        st.rerun()
# --- 5. THE CHAT ENGINE ---
st.title("🤖 FreDèlAi")

# 1. UI History Display
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# 2. Vision Upload
up_file = st.file_uploader("📎 Vision Upload", type=['png', 'jpg', 'jpeg'], key="vision_up", label_visibility="collapsed")

if prompt := st.chat_input("Ask or teach a pattern..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # SQLite Logic (TAII Check)
    if " is " in prompt.lower() and len(prompt.split()) < 10:
        parts = prompt.lower().split(" is ", 1)
        k, v = parts[0].strip(), parts[1].strip()
        save_pattern(k, v)
        st.session_state.patterns = load_mem() 
        st.toast(f"🧠 Pattern '{k}' saved!")

    # 3. AI RESPONSE
    with st.chat_message("assistant"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            
            # Prepare Hidden Context from SQLite
            mem_data = st.session_state.patterns
            context_string = ", ".join([f"{k}:{v}" for k,v in mem_data.items()])
            
            sys_prompt = (
                f"You are FreDèlAi, assistant to DELU. Context: {context_string}. "
                "Your name is FreDèlAi. Keep it 'Noice'. "
                "Worksheets must be exactly 15 sentences. AK must be full sentences."
            )

            # --- THE FINAL FIX: EVERYTHING IS A STRING ---
            if up_file:
                st.image(up_file, width=250)
                # We append the image data as a string reference within the prompt 
                # rather than a complex object list, to satisfy the 'must be string' rule.
                img_b64 = encode_img(up_file)
                full_user_text = f"{prompt} [Attached Image Data: data:image/jpeg;base64,{img_b64}]"
            else:
                full_user_text = str(prompt)

            # API Call - Strictly sending strings only
            response = client.chat.completions.create(
                model=MAVERICK,
                messages=[
                    {"role": "system", "content": str(sys_prompt)},
                    {"role": "user", "content": full_user_text} # This is now GUARANTEED to be a string
                ]
            )
            
            res_text = response.choices[0].message.content
            st.markdown(res_text)
            st.session_state.messages.append({"role": "assistant", "content": res_text})
            
        except Exception as e:
            st.error(f"Error: Please Call FreDel Classes Official Tech Support. ({str(e)})")
