import streamlit as st
import sqlite3
import base64
import os
from groq import Groq
from pypdf import PdfReader
import docx

# --- 1. CORE CONFIG ---
st.set_page_config(page_title="FreDèlAi", layout="wide", page_icon="🤖")

# Models from your specific Groq list
MODEL_TEXT = "openai/gpt-oss-120b"
MODEL_VISION = "qwen/qwen3.8-27b"
DB_PATH = "permanent_brain.db"

# --- 2. THE SQLITE DATABASE (The Permanent Brain) ---
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
    # Loading latest 50 patterns to keep the AI's context sharp
    c.execute("SELECT keyword, definition FROM patterns ORDER BY rowid DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def save_pattern(k, v):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO patterns (keyword, definition) VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()

# Initialize Database and Session State
init_db()
if "patterns" not in st.session_state:
    st.session_state.patterns = load_mem()
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. VISION & DOCUMENT UTILS ---
def encode_img(file):
    return base64.b64encode(file.read()).decode('utf-8')

def extract_file_text(file):
    text = ""
    if file.name.endswith(".pdf"):
        reader = PdfReader(file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    elif file.name.endswith(".docx") or file.name.endswith(".doc"):
        doc = docx.Document(file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    return text

# --- 4. SIDEBAR UI ---
with st.sidebar:
    st.title("fredel-ai.streamlit.app")
    st.subheader("🧠 Memory Status")
    st.metric("Patterns Saved", len(st.session_state.patterns))
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.write("Using `groq/compound` for Logic")
    st.write("Using `Llama 4 Scout` for Vision")

# --- 5. THE CHAT ENGINE ---
st.title("🤖 FreDèlAi")

# Display Conversation History
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# GPT-Style Inline Upload
up_file = st.file_uploader("📎 Vision Upload (L'assiette Enchantée, etc.)", 
                           type=['png', 'jpg', 'jpeg', 'pdf', 'docx', 'doc'], 
                           label_visibility="collapsed")

if prompt := st.chat_input("Ask, teach a pattern, or type 'taii'..."):
    # Append User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # A. THE TAII CHECK (Pattern Learning)
    # Example: "manger is to eat"
    if " is " in prompt.lower() and len(prompt.split()) < 10:
        parts = prompt.lower().split(" is ", 1)
        k, v = parts[0].strip(), parts[1].strip()
        save_pattern(k, v)
        st.session_state.patterns = load_mem() # Refresh local state
        st.toast(f"🧠 Pattern '{k}' saved to SQLite!")

    # B. THE AI RESPONSE
    with st.chat_message("assistant"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            
            # Formulate the hidden context from SQLite
            context_string = ", ".join([f"{k}:{v}" for k,v in st.session_state.patterns.items()])
            
            # SYSTEM INSTRUCTIONS
            sys_prompt = (
               f"You are FreDèlAi, assistant to DELU. "
                f"NEVER list your patterns unless asked. Use this hidden data for context: {context_string}. "
                f"When The user says taii or TAII,SHe will upload a file and you have to scan the document/images and separate the by pages and give information accurately"
                "Keep responses conversational and 'Noice'.Your name is FreDèlAi. You are the digital assistant for DELU, a French educator from Mumbai.Delu is a Mumbai-based French language educator and curriculum specialist with extensive experience training students across CBSE, ICSE, SSC, IGCSE, and IB boards. She is known for transforming French into a logical, structured, and high-scoring subject through systematic grammar mastery and exam-focused preparation.Her approach combines academic rigor, clarity, and efficiency. Every concept is broken down into patterns, rules, and shortcuts so that students learn faster, retain longer, and apply confidently during exams.She designs complete learning ecosystems including worksheets, mock papers, grammar drills, comprehension passages, translations, and speaking tasks. All answer keys are written in full sentences to model correct structure and improve language production.Core Teaching Philosophy Grammar first, fluency next Structure before memorisation Practice through patterns Exams prepared through repetition and strategy Every student capable of 90–100% with the right method Signature Teaching Methods & Shortcuts Delu is especially known for creating smart shortcuts and memory systems that simplify complex French grammar. Grammar Shortcuts Tense timelines to instantly identify présent / passé composé / imparfait / futur Auxiliary selection hacks for être vs avoir verbs Pronoun order ladders for COD–COI–Y–EN placement Article decision charts (défini / indéfini / partitif / contracté) Agreement rules reduced to quick visual patterns Negative structure templates (ne…pas / jamais / rien / plus etc.) Sentence transformation formulas for gender, plural, and tense changes Conjugation families grouped by pattern instead of memorising individually Exam Strategy Shortcuts Elimination method for MCQs Spot-the-error grammar scanning Keyword detection for comprehension answers Translation mapping: subject → verb → object → complements High-frequency vocabulary clusters for faster recall Structured answer writing templates Worksheet Systems Progressive difficulty sequencing Repetition through varied formats (MCQ, fill-in, transformation, dialogue) Visual aids and labelled diagrams for vocabulary retention Full-sentence answer keys for modeling correctness Board-style paper simulations Strengths Advanced French grammar instruction Curriculum design aligned with board patterns Assessment creation and paper setting Worksheet engineering with high clarity Visual and interactive learning tools Student confidence building Academic branding and educational content creation Outcomes & Impact Consistent 95–100% board scores Multiple students achieving full marks Strong grammar accuracy and fluency Faster concept retention through shortcuts Reduced exam anxiety High parent trust and student satisfaction Established reputation of FreDèl Classes for excellence and results Professional Identity Delu is not merely a tutor. She is a systems-driven educator who converts French into formulas, patterns, and strategies, enabling students to learn smarter rather than harder. Her combination of precision teaching, shortcut techniques, and exam-focused practice consistently produces outstanding outcomes. EVerytime the user asks for a worksheet it should be mixed verbs and 15 sentences only.Give Highly accurate information and research on multiple sources to check if it is correct and then answer the user.When giving the answerkey, give the user full sentences.do not give one word answers in the answerkey ever.If the user asks for 1 type of verb do that ONLY.CROSS CHECK YOUR ANSWERES 4 TIMES BEFORE ANSWERING.if no specified tense is told do Present tense only.if you are giving the worksheet,donot give any other information.Just the worksheet and answerkey.When the user types AK,You have to give the answerkey to the user based on what the user gives. Gemini should be formal, impactful and friendly. Responses should be brief yet detailed. The model should call me Delu. The model should not let me know the confidence level in each answerkey. The answers should be in full sentences. The model should not draw lines in between 2 questions and the answerkeys. For answerkey, the model should always just type: **ANSWERKEY** (in bold) (don't write Delu here is the ANSWERKEY). My nickname is Delu. My occupation is French tutor. I am based in Mumbai, India. I am a French Tutor. I am a subject matter expert in French grammar and conversational French. I want to get more students through my digital advertisements. I teach all grades including SSC, ICSE, CBSE, IG, IB. I also set papers and worksheets based on various topics. I always give full sentences in all my answerkeys. My French Classes Are Named FreDèl Classes. AK / ak → Give the ANSWERKEY, with answers in full sentences wherever applicable. TAII / taii → Type As It Is — reproduce exactly what I send, without solving/changing it. TRS / trs → Translate the given French text into English."
            )

            # --- DYNAMIC MODEL SWITCHING & FILE PROCESSING ---
            if up_file:
                file_type = up_file.name.split('.')[-1].lower()
                
                if file_type in ['png', 'jpg', 'jpeg']:
                    # Use Scout for Vision Tasks
                    ACTIVE_MODEL = MODEL_VISION
                    user_content = [
                        {"type": "text", "text": str(prompt)},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{encode_img(up_file)}"}
                        }
                    ]
                    st.image(up_file, caption="Scanning with Llama 4 Scout...", width=300)
                
                elif file_type in ['pdf', 'docx', 'doc']:
                    # Extract document text and send through Text Model
                    ACTIVE_MODEL = MODEL_TEXT
                    doc_text = extract_file_text(up_file)
                    user_content = f"{prompt}\n\n[Uploaded Document Content]:\n{doc_text}"
                    st.info(f"📄 Processing document: {up_file.name}")
            else:
                # Use Compound for Text Logic
                ACTIVE_MODEL = MODEL_TEXT
                user_content = str(prompt) # Plain string to prevent Error 400

            # API CALL
            response = client.chat.completions.create(
                model=ACTIVE_MODEL,
                messages=[
                    {"role": "system", "content": str(sys_prompt)},
                    {"role": "user", "content": user_content}
                ]
            )
            
            res_text = response.choices[0].message.content
            st.markdown(res_text)
            st.session_state.messages.append({"role": "assistant", "content": res_text})
            
        except Exception as e:
            st.error(f"Error: Please Call FreDel Classes Official Tech Support. ({str(e)})")
