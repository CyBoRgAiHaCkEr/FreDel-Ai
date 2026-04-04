import streamlit as st
import sqlite3
import base64
import os
from groq import Groq

# --- 1. CORE CONFIG ---
st.set_page_config(page_title="FreDèlAi", layout="wide")

MODEL_ID = "groq/compound" # Ensure you use a vision-capable model
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

# Initialize DB and Session State
init_db()
if "patterns" not in st.session_state:
    st.session_state.patterns = load_mem()
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. VISION & UI ---
def encode_img(file):
    return base64.b64encode(file.read()).decode('utf-8')

with st.sidebar:
    st.title("fredel-ai.streamlit.app")
    st.subheader("Settings")
    french_mode = st.toggle("🇫🇷 French Mode", value=False)
    st.divider()
    st.metric("Patterns in Memory", len(st.session_state.patterns))
    if st.button("Refresh Memory"):
        st.session_state.patterns = load_mem()
        st.rerun()

# --- 4. THE CHAT ENGINE ---
st.title("🤖 FreDèlAi")

# Display History
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Inline Upload
up_file = st.file_uploader("📎 Vision Upload", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")

if prompt := st.chat_input("Ask or teach a pattern..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # A. THE TAII CHECK (Save to SQLite)
    if " is " in prompt.lower() and len(prompt.split()) < 10:
        parts = prompt.lower().split(" is ", 1)
        k, v = parts[0].strip(), parts[1].strip()
        save_pattern(k, v)
        st.session_state.patterns = load_mem() # Refresh state
        st.toast(f"🧠 Pattern '{k}' saved to permanent brain!")

 # B. THE AI RESPONSE
    with st.chat_message("assistant"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            
            # 1. Prepare context from SQLite memory
            context_string = ", ".join([f"{k}:{v}" for k,v in st.session_state.patterns.items()])
            
            # 2. Define the sys_prompt clearly so it's always available
            sys_prompt = (
                f"You are FreDèlAi, assistant to DELU. "
                f"NEVER list your patterns unless asked. Use this hidden data for context: {context_string}. "
                "Keep responses conversational and 'Noice'. Your name is FreDèlAi. "
                "Delu is a French educator from Mumbai... (keep your full detailed prompt here)"
            )

            # 3. Handle Content Type (THE FIX)
            if up_file:
                # VISION MODE: Requires a list of objects
                user_content = [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{encode_img(up_file)}"}
                    }
                ]
                st.image(up_file, width=250)
            else:
                # TEXT MODE: Groq requires a simple string to avoid Error 400
                user_content = str(prompt) 

            # 4. API Call
            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_content}
                ]
            )
            
            res_text = response.choices[0].message.content
            st.markdown(res_text)
            st.session_state.messages.append({"role": "assistant", "content": res_text})
            
        except Exception as e:
            st.error(f"Error: Please Call FreDel Classes Official Tech Support. ({str(e)})")
