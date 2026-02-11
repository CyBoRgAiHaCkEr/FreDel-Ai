import streamlit as st
import json, socket
from groq import Groq
from PIL import Image
import pdfplumber

# --- 1. SETTINGS & IDENTITY ---
st.set_page_config(page_title="FreDèlAi", layout="wide")

# The "Best, The One, The Only" Model Selection
LLAMA4_SCOUT = "meta-llama/llama-4-scout-17b-16e-instruct"
IDENTITY = "Your name is FreDèlAi. You are the digital assistant for DELU, a French educator from Mumbai.taii means she will upload an images and you have to scan them and type the text as it is.if she uploads multiple images or files like pdfs or presentations,separate the text page by page.Delu is a Mumbai-based French language educator and curriculum specialist with extensive experience training students across CBSE, ICSE, SSC, IGCSE, and IB boards. She is known for transforming French into a logical, structured, and high-scoring subject through systematic grammar mastery and exam-focused preparation.Her approach combines academic rigor, clarity, and efficiency. Every concept is broken down into patterns, rules, and shortcuts so that students learn faster, retain longer, and apply confidently during exams.She designs complete learning ecosystems including worksheets, mock papers, grammar drills, comprehension passages, translations, and speaking tasks. All answer keys are written in full sentences to model correct structure and improve language production.Core Teaching Philosophy Grammar first, fluency next Structure before memorisation Practice through patterns Exams prepared through repetition and strategy Every student capable of 90–100% with the right method Signature Teaching Methods & Shortcuts Delu is especially known for creating smart shortcuts and memory systems that simplify complex French grammar. Grammar Shortcuts Tense timelines to instantly identify présent / passé composé / imparfait / futur Auxiliary selection hacks for être vs avoir verbs Pronoun order ladders for COD–COI–Y–EN placement Article decision charts (défini / indéfini / partitif / contracté) Agreement rules reduced to quick visual patterns Negative structure templates (ne…pas / jamais / rien / plus etc.) Sentence transformation formulas for gender, plural, and tense changes Conjugation families grouped by pattern instead of memorising individually Exam Strategy Shortcuts Elimination method for MCQs Spot-the-error grammar scanning Keyword detection for comprehension answers Translation mapping: subject → verb → object → complements High-frequency vocabulary clusters for faster recall Structured answer writing templates Worksheet Systems Progressive difficulty sequencing Repetition through varied formats (MCQ, fill-in, transformation, dialogue) Visual aids and labelled diagrams for vocabulary retention Full-sentence answer keys for modeling correctness Board-style paper simulations Strengths Advanced French grammar instruction Curriculum design aligned with board patterns Assessment creation and paper setting Worksheet engineering with high clarity Visual and interactive learning tools Student confidence building Academic branding and educational content creation Outcomes & Impact Consistent 95–100% board scores Multiple students achieving full marks Strong grammar accuracy and fluency Faster concept retention through shortcuts Reduced exam anxiety High parent trust and student satisfaction Established reputation of FreDèl Classes for excellence and results Professional Identity Delu is not merely a tutor. She is a systems-driven educator who converts French into formulas, patterns, and strategies, enabling students to learn smarter rather than harder. Her combination of precision teaching, shortcut techniques, and exam-focused practice consistently produces outstanding outcomes."

if "messages" not in st.session_state: st.session_state.messages = []
if "patterns" not in st.session_state: st.session_state.patterns = {}

# --- 2. THE PANIC/REPAIR ENGINE ---
def run_repair():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        client.models.list()
        return True, "✅ System Repaired! Connection to Llama-4-Scout is active."
    except Exception as e:
        return False, f"❌ Repair Failed: {str(e)}"

# --- 3. INLINE UPLOAD & CHAT (Like ChatGPT) ---
st.title("🤖 FreDèlAi")
st.caption(f"Powered by {LLAMA4_SCOUT}")

# Sidebar now only for search/memory view
with st.sidebar:
    st.title("🧠 Pattern Memory")
    search = st.text_input("🔍 Quick Search")
    if search and search.lower() in st.session_state.patterns:
        st.success(st.session_state.patterns[search.lower()])
    st.metric("Stored", len(st.session_state.patterns))
    if st.button("🛠️ PANIC: Repair Connection"):
        ok, msg = run_repair()
        st.toast(msg)

# Display Chat History
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# FILE UPLOADER (Inline, above the text bar)
uploaded_file = st.file_uploader("📎 Attach a worksheet for taii", type=['pdf', 'png', 'jpg', 'txt'], label_visibility="collapsed")

if prompt := st.chat_input("Ask FreDèlAi or upload a file..."):
    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # PROCESS UPLOADED FILE CONTENT
    file_content = ""
    if uploaded_file:
        with st.spinner("Reading file..."):
            if uploaded_file.type == "application/pdf":
                with pdfplumber.open(uploaded_file) as pdf:
                    file_content = "\\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            elif "image" in uploaded_file.type:
                file_content = "[Image attached - OCR processing placeholder]" # Add EasyOCR here if needed
            else:
                file_content = uploaded_file.read().decode()
        st.toast("File attached to query!")

    # SHORTCUT CHECK (taii is...)
    if " is " in prompt.lower() and len(prompt.split()) < 12:
        k, v = prompt.lower().split(" is ", 1)
        st.session_state.patterns[k.strip()] = v.strip()
        st.toast("Pattern Memorized!")

    # CALL LLAMA-4-SCOUT
    with st.chat_message("assistant"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            
            # Combine prompt with file content
            full_prompt = f"FILE CONTENT: {file_content}\\n\\nUSER QUESTION: {prompt}" if file_content else prompt
            
            response = client.chat.completions.create(
                model=LLAMA4_SCOUT,
                messages=[{"role": "system", "content": IDENTITY}] + 
                         st.session_state.messages[-5:] + 
                         [{"role": "user", "content": full_prompt}],
                temperature=0.7
            )
            
            ans = response.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
        except Exception as e:
            st.error("🚨 Connection Glitch! The Llama-4-Scout brain is unreachable.")
            if st.button("🔧 Solve the error now"):
                ok, msg = run_repair()
                if ok: st.rerun()
