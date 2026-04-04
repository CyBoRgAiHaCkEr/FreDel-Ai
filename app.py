import streamlit as st
import sqlite3, base64, os
from groq import Groq

# --- 1. CORE CONFIG ---
st.set_page_config(page_title="FreDèlAi", layout="wide")
MAVERICK = "meta-llama/llama-4-scout-17b-16e-instruct" 
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
    # LIMIT to last 20 patterns so the prompt doesn't get too long
    c.execute("SELECT keyword, definition FROM patterns ORDER BY rowid DESC LIMIT 20")
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

# --- 3. VISION (ONLY FOR DISPLAY) ---
def encode_img(file):
    return base64.b64encode(file.read()).decode('utf-8')

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("fredel-ai.streamlit.app")
    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()

# --- 5. THE CHAT ENGINE ---
st.title("🤖 FreDèlAi")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

up_file = st.file_uploader("📎 Vision Upload", type=['png', 'jpg', 'jpeg'], key="vision_up")

if prompt := st.chat_input("Ask or teach..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # TAII CHECK
    if " is " in prompt.lower() and len(prompt.split()) < 10:
        k, v = prompt.lower().split(" is ", 1)
        save_pattern(k.strip(), v.strip())
        st.session_state.patterns = load_mem()
        st.toast("🧠 Pattern saved!")

    # AI RESPONSE
    with st.chat_message("assistant"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            
            # Shorten context to avoid "Length" error
            context_string = ", ".join([f"{k}:{v}" for k,v in st.session_state.patterns.items()])
            
            sys_prompt = (
                f"You are FreDèlAi for DELU. Context: {context_string}. "
                "Responses: 'Noice'. Worksheets: 15 sentences. AK: Full sentences."
            )

            # --- THE FIX: NO BASE64 IN THE PROMPT ---
            if up_file:
                st.image(up_file, width=250)
                # We tell the AI an image exists, but we DON'T send the huge Base64 string
                # because groq/compound is likely a text-only endpoint.
                final_prompt = f"[User uploaded an image] {prompt}"
            else:
                final_prompt = str(prompt)

            response = client.chat.completions.create(
                model=MAVERICK,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": final_prompt}
                ]
            )
            
            res_text = response.choices[0].message.content
            st.markdown(res_text)
            st.session_state.messages.append({"role": "assistant", "content": res_text})
            
        except Exception as e:
            st.error(f"Error: Please Call FreDel Classes Official Tech Support. ({str(e)})")
