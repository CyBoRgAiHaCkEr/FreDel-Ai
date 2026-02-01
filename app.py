import streamlit as st
import os, json, requests, base64, time
import pdfplumber, easyocr, cv2
import numpy as np
from PIL import Image
from groq import Groq

# --- 1. SYSTEM CONFIG ---
st.set_page_config(page_title="FreDèlAi", layout="wide")

# This is your 3500+ command storage
if "patterns" not in st.session_state: st.session_state.patterns = {}
if "messages" not in st.session_state: st.session_state.messages = []
if "brain_memory" not in st.session_state: 
    st.session_state.brain_memory = "Your name is FreDèlAi. You are the digital assistant for DELU, a French educator from Mumbai.Delu is a Mumbai-based French language educator and curriculum specialist with extensive experience training students across CBSE, ICSE, SSC, IGCSE, and IB boards. She is known for transforming French into a logical, structured, and high-scoring subject through systematic grammar mastery and exam-focused preparation.Her approach combines academic rigor, clarity, and efficiency. Every concept is broken down into patterns, rules, and shortcuts so that students learn faster, retain longer, and apply confidently during exams.She designs complete learning ecosystems including worksheets, mock papers, grammar drills, comprehension passages, translations, and speaking tasks. All answer keys are written in full sentences to model correct structure and improve language production.Core Teaching Philosophy Grammar first, fluency next Structure before memorisation Practice through patterns Exams prepared through repetition and strategy Every student capable of 90–100% with the right method Signature Teaching Methods & Shortcuts Delu is especially known for creating smart shortcuts and memory systems that simplify complex French grammar. Grammar Shortcuts Tense timelines to instantly identify présent / passé composé / imparfait / futur Auxiliary selection hacks for être vs avoir verbs Pronoun order ladders for COD–COI–Y–EN placement Article decision charts (défini / indéfini / partitif / contracté) Agreement rules reduced to quick visual patterns Negative structure templates (ne…pas / jamais / rien / plus etc.) Sentence transformation formulas for gender, plural, and tense changes Conjugation families grouped by pattern instead of memorising individually Exam Strategy Shortcuts Elimination method for MCQs Spot-the-error grammar scanning Keyword detection for comprehension answers Translation mapping: subject → verb → object → complements High-frequency vocabulary clusters for faster recall Structured answer writing templates Worksheet Systems Progressive difficulty sequencing Repetition through varied formats (MCQ, fill-in, transformation, dialogue) Visual aids and labelled diagrams for vocabulary retention Full-sentence answer keys for modeling correctness Board-style paper simulations Strengths Advanced French grammar instruction Curriculum design aligned with board patterns Assessment creation and paper setting Worksheet engineering with high clarity Visual and interactive learning tools Student confidence building Academic branding and educational content creation Outcomes & Impact Consistent 95–100% board scores Multiple students achieving full marks Strong grammar accuracy and fluency Faster concept retention through shortcuts Reduced exam anxiety High parent trust and student satisfaction Established reputation of FreDèl Classes for excellence and results Professional Identity Delu is not merely a tutor. She is a systems-driven educator who converts French into formulas, patterns, and strategies, enabling students to learn smarter rather than harder. Her combination of precision teaching, shortcut techniques, and exam-focused practice consistently produces outstanding outcomes."

# --- 2. SIDEBAR (LOGS & DATA) ---
with st.sidebar:
    if os.path.exists("logo.jpg"): st.image("logo.jpg", width='stretch')
    elif os.path.exists("logo.png"): st.image("logo.png", width='stretch')
    
    st.title("FreDèlAi")
    
    # Show memory usage
    mem_count = len(st.session_state.patterns)
    st.write(f"🧠 Memory Slots Used: {mem_count} / 5500")
    
    st.divider()
    st.subheader("💾 Hard Memory Sync")
    # Download everything (Bio + all 3500 commands)
    full_data = {"mem": st.session_state.brain_memory, "patterns": st.session_state.patterns}
    st.download_button("📥 Export Brain (.json)", data=json.dumps(full_data), file_name="delu_infinite_brain.json")
    
    up_brain = st.file_uploader("📤 Import Brain", type="json")
    if up_brain and st.button("🔄 Overwrite Memory"):
        b = json.load(up_brain)
        st.session_state.brain_memory = b.get('mem', "")
        st.session_state.patterns = b.get('patterns', {})
        st.rerun()

    st.divider()
    # OCR Section
    st.subheader("🔍 OCR Worksheet Sync")
    files = st.file_uploader("Upload Knowledge", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("⚡ Process & Remember"):
        reader = easyocr.Reader(['en', 'fr'], gpu=False)
        for f in files:
            if "pdf" in f.type:
                with pdfplumber.open(f) as pdf:
                    txt = " ".join([p.extract_text() or "" for p in pdf.pages])
            else:
                img = np.array(Image.open(f))
                txt = " ".join(reader.readtext(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), detail=0))
            st.session_state.brain_memory += f"\n[FILE: {f.name}]: {txt}"
        st.success("OCR Knowledge Integrated!")

# --- 3. THE COMMAND & CHAT ENGINE ---

# Display chat history
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Enter command or chat with Delu's assistant..."):
    # Log user input
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # --- STEP 1: CHECK FOR COMMAND ASSIGNMENT (X is Y) ---
    if " is " in prompt.lower() and len(prompt.split()) < 30:
        key, val = prompt.lower().split(" is ", 1)
        st.session_state.patterns[key.strip()] = val.strip()
        response = f"✅ Learned! Command '{key.strip()}' now triggers your text. ({len(st.session_state.patterns)}/3500 used)"
        with st.chat_message("assistant"): st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

    # --- STEP 2: CHECK FOR COMMAND TRIGGER (e.g. 'taii') ---
    elif prompt.lower().strip() in st.session_state.patterns:
        # BYPASS AI ENTIRELY: Print exact text from memory
        final_output = st.session_state.patterns[prompt.lower().strip()]
        with st.chat_message("assistant"): st.markdown(final_output)
        st.session_state.messages.append({"role": "assistant", "content": final_output})

    # --- STEP 3: NORMAL CHAT (If not a command) ---
    else:
        with st.chat_message("assistant"):
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                # Feed the AI all the background info but keep recent chat short to save speed
                sys_msg = (
                    f"You are FreDèlAi, the assistant for expert French teacher DELU. "
                    f"Background Knowledge: {st.session_state.brain_memory[-2000:]}. "
                    "Always refer to Delu as the boss/teacher. Be professional and concise."
                )
                r = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[{"role":"system","content":sys_msg}] + st.session_state.messages[-10:]
                )
                ans = r.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except:
                st.error("API Busy. Try again in a moment.")

# Keep chat clean - only store last 50 messages to keep the app fast
if len(st.session_state.messages) > 50:
    st.session_state.messages = st.session_state.messages[-50:]
