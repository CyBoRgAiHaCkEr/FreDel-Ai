import streamlit as st
import os, numpy as np, requests, time, json, base64
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq

# --- 1. CONFIG ---
st.set_page_config(page_title="FreDèlAi", layout="wide")

if "messages" not in st.session_state: st.session_state.messages = []
if "patterns" not in st.session_state: st.session_state.patterns = {}
if "brain_memory" not in st.session_state: 
    st.session_state.brain_memory = "Your name is FreDèlAi. You are the digital assistant for DELU, a French educator from Mumbai.Delu is a Mumbai-based French language educator and curriculum specialist with extensive experience training students across CBSE, ICSE, SSC, IGCSE, and IB boards. She is known for transforming French into a logical, structured, and high-scoring subject through systematic grammar mastery and exam-focused preparation.Her approach combines academic rigor, clarity, and efficiency. Every concept is broken down into patterns, rules, and shortcuts so that students learn faster, retain longer, and apply confidently during exams.She designs complete learning ecosystems including worksheets, mock papers, grammar drills, comprehension passages, translations, and speaking tasks. All answer keys are written in full sentences to model correct structure and improve language production.Core Teaching Philosophy Grammar first, fluency next Structure before memorisation Practice through patterns Exams prepared through repetition and strategy Every student capable of 90–100% with the right method Signature Teaching Methods & Shortcuts Delu is especially known for creating smart shortcuts and memory systems that simplify complex French grammar. Grammar Shortcuts Tense timelines to instantly identify présent / passé composé / imparfait / futur Auxiliary selection hacks for être vs avoir verbs Pronoun order ladders for COD–COI–Y–EN placement Article decision charts (défini / indéfini / partitif / contracté) Agreement rules reduced to quick visual patterns Negative structure templates (ne…pas / jamais / rien / plus etc.) Sentence transformation formulas for gender, plural, and tense changes Conjugation families grouped by pattern instead of memorising individually Exam Strategy Shortcuts Elimination method for MCQs Spot-the-error grammar scanning Keyword detection for comprehension answers Translation mapping: subject → verb → object → complements High-frequency vocabulary clusters for faster recall Structured answer writing templates Worksheet Systems Progressive difficulty sequencing Repetition through varied formats (MCQ, fill-in, transformation, dialogue) Visual aids and labelled diagrams for vocabulary retention Full-sentence answer keys for modeling correctness Board-style paper simulations Strengths Advanced French grammar instruction Curriculum design aligned with board patterns Assessment creation and paper setting Worksheet engineering with high clarity Visual and interactive learning tools Student confidence building Academic branding and educational content creation Outcomes & Impact Consistent 95–100% board scores Multiple students achieving full marks Strong grammar accuracy and fluency Faster concept retention through shortcuts Reduced exam anxiety High parent trust and student satisfaction Established reputation of FreDèl Classes for excellence and results Professional Identity Delu is not merely a tutor. She is a systems-driven educator who converts French into formulas, patterns, and strategies, enabling students to learn smarter rather than harder. Her combination of precision teaching, shortcut techniques, and exam-focused practice consistently produces outstanding outcomes."

# --- 2. SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.jpg"): st.image("logo.jpg", width='stretch')
    elif os.path.exists("logo.png"): st.image("logo.png", width='stretch')
    
    st.divider()
    st.subheader("💾 Memory Management")
    brain_data = {"mem": st.session_state.brain_memory, "patterns": st.session_state.patterns}
    st.download_button("📥 Download Brain", data=json.dumps(brain_data), file_name="delu_memory.json")
    
    up_brain = st.file_uploader("📤 Upload Brain", type="json")
    if up_brain and st.button("🔄 Sync"):
        b = json.load(up_brain)
        st.session_state.brain_memory = b.get('mem', "")
        st.session_state.patterns = b.get('patterns', {})
        st.rerun()

    st.divider()
    st.subheader("🔍 OCR (Worksheet Reader)")
    is_fr = st.toggle("French Mode", value=False)
    files = st.file_uploader("Upload PDFs/Images", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("⚡ Process Files"):
        reader = easyocr.Reader(['en', 'fr'] if is_fr else ['en'], gpu=False)
        for f in files:
            if "pdf" in f.type:
                with pdfplumber.open(f) as pdf:
                    txt = " ".join([p.extract_text() or "" for p in pdf.pages])
            else:
                img = np.array(Image.open(f))
                txt = " ".join(reader.readtext(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), detail=0))
            st.session_state.brain_memory += f"\n[Doc: {f.name}]: {txt}"
        st.success("Files saved to memory!")

# --- 3. THE CHAT ENGINE ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Message..."):
    # USER MESSAGE
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # --- HARD OVERRIDE LOGIC ---
    # 1. SETTING A SHORTCUT (e.g., taii is ...)
    if " is " in prompt.lower() and len(prompt.split()) < 30:
        key, val = prompt.lower().split(" is ", 1)
        st.session_state.patterns[key.strip()] = val.strip()
        msg = f"✅ Saved! Whenever you type '{key.strip()}', I will output that exact text."
        with st.chat_message("assistant"): st.markdown(msg)
        st.session_state.messages.append({"role": "assistant", "content": msg})

    # 2. USING A SHORTCUT (e.g., typing 'taii')
    elif prompt.lower().strip() in st.session_state.patterns:
        output = st.session_state.patterns[prompt.lower().strip()]
        with st.chat_message("assistant"): st.markdown(output)
        st.session_state.messages.append({"role": "assistant", "content": output})

    # 3. NORMAL CHAT (AI AS DELU'S ASSISTANT)
    else:
        with st.chat_message("assistant"):
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                sys_msg = (
                    f"You are FreDèlAi, the digital assistant created by the educator DELU. "
                    f"Knowledge: {st.session_state.brain_memory}. "
                    "Always refer to Delu as the expert teacher. Answer concisely and professionally."
                )
                r = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"system","content":sys_msg}] + st.session_state.messages[-6:]
                )
                ans = r.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except:
                st.error("API Error.")
