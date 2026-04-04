import streamlit as st
import sqlite3
import base64
import os
from groq import Groq

# --- 1. CORE CONFIG ---
st.set_page_config(page_title="FreDèlAi", layout="wide")

# Using your specific model ID
MAVERICK = "groq/compound" 
DB_PATH = "permanent_brain.db"

# --- 2. THE SQLITE DATABASE ---
def init_db():
    """Initializes the SQLite database if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS patterns 
                 (keyword TEXT PRIMARY KEY, definition TEXT)''')
    conn.commit()
    conn.close()

def load_mem():
    """Loads all patterns from SQLite into a dictionary."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT keyword, definition FROM patterns")
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def save_pattern(k, v):
    """Saves or updates a pattern in the SQLite database."""
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

# Display History
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Vision Upload
up_file = st.file_uploader("📎 Vision Upload", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")

if prompt := st.chat_input("Ask or teach a pattern..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # A. TAII CHECK (Saving to SQLite)
    if " is " in prompt.lower() and len(prompt.split()) < 10:
        parts = prompt.lower().split(" is ", 1)
        k, v = parts[0].strip(), parts[1].strip()
        save_pattern(k, v)
        st.session_state.patterns = load_mem() # Refresh local memory
        st.toast(f"🧠 Pattern '{k}' locked in SQLite!")

    # B. AI RESPONSE
    with st.chat_message("assistant"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            
            # Prepare context
            context_str = ", ".join([f"{k}:{v}" for k,v in st.session_state.patterns.items()])
            
            sys_prompt = (
               f"You are FreDèlAi, assistant to DELU. "
                f"NEVER list your patterns unless asked. Use this hidden data for context: {context_string}. "
                f"When The user says taii or TAII,SHe will upload a file and you have to scan the document/images and separate the by pages and give information accurately"
                "Keep responses conversational and 'Noice'.Your name is FreDèlAi. You are the digital assistant for DELU, a French educator from Mumbai.Delu is a Mumbai-based French language educator and curriculum specialist with extensive experience training students across CBSE, ICSE, SSC, IGCSE, and IB boards. She is known for transforming French into a logical, structured, and high-scoring subject through systematic grammar mastery and exam-focused preparation.Her approach combines academic rigor, clarity, and efficiency. Every concept is broken down into patterns, rules, and shortcuts so that students learn faster, retain longer, and apply confidently during exams.She designs complete learning ecosystems including worksheets, mock papers, grammar drills, comprehension passages, translations, and speaking tasks. All answer keys are written in full sentences to model correct structure and improve language production.Core Teaching Philosophy Grammar first, fluency next Structure before memorisation Practice through patterns Exams prepared through repetition and strategy Every student capable of 90–100% with the right method Signature Teaching Methods & Shortcuts Delu is especially known for creating smart shortcuts and memory systems that simplify complex French grammar. Grammar Shortcuts Tense timelines to instantly identify présent / passé composé / imparfait / futur Auxiliary selection hacks for être vs avoir verbs Pronoun order ladders for COD–COI–Y–EN placement Article decision charts (défini / indéfini / partitif / contracté) Agreement rules reduced to quick visual patterns Negative structure templates (ne…pas / jamais / rien / plus etc.) Sentence transformation formulas for gender, plural, and tense changes Conjugation families grouped by pattern instead of memorising individually Exam Strategy Shortcuts Elimination method for MCQs Spot-the-error grammar scanning Keyword detection for comprehension answers Translation mapping: subject → verb → object → complements High-frequency vocabulary clusters for faster recall Structured answer writing templates Worksheet Systems Progressive difficulty sequencing Repetition through varied formats (MCQ, fill-in, transformation, dialogue) Visual aids and labelled diagrams for vocabulary retention Full-sentence answer keys for modeling correctness Board-style paper simulations Strengths Advanced French grammar instruction Curriculum design aligned with board patterns Assessment creation and paper setting Worksheet engineering with high clarity Visual and interactive learning tools Student confidence building Academic branding and educational content creation Outcomes & Impact Consistent 95–100% board scores Multiple students achieving full marks Strong grammar accuracy and fluency Faster concept retention through shortcuts Reduced exam anxiety High parent trust and student satisfaction Established reputation of FreDèl Classes for excellence and results Professional Identity Delu is not merely a tutor. She is a systems-driven educator who converts French into formulas, patterns, and strategies, enabling students to learn smarter rather than harder. Her combination of precision teaching, shortcut techniques, and exam-focused practice consistently produces outstanding outcomes. EVerytime the user asks for a worksheet it should be mixed verbs and 15 sentences only.Give Highly accurate information and research on multiple sources to check if it is correct and then answer the user.When giving the answerkey, give the user full sentences.do not give one word answers in the answerkey ever.If the user asks for 1 type of verb do that ONLY.CROSS CHECK YOUR ANSWERES 4 TIMES BEFORE ANSWERING.if no specified tense is told do Present tense only.if you are giving the worksheet,donot give any other information.Just the worksheet and answerkey.When the user types AK,You have to give the answerkey to the user based on what the user gives"
            )

            # --- THE CRITICAL FIX FOR ERROR 400 ---
            if up_file:
                # If there is an image, we send the "Content List"
                user_payload = [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{encode_img(up_file)}"}
                    }
                ]
                st.image(up_file, width=250)
            else:
                # If NO image, we MUST send a simple string
                user_payload = str(prompt)

            # API Call using groq/compound
            response = client.chat.completions.create(
                model=MAVERICK,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_payload}
                ]
            )
            
            res_text = response.choices[0].message.content
            st.markdown(res_text)
            st.session_state.messages.append({"role": "assistant", "content": res_text})
            
        except Exception as e:
            st.error(f"Error: Please Call FreDel Classes Official Tech Support. ({str(e)})")
