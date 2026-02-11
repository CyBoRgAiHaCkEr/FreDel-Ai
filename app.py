import streamlit as st
import json, base64, os
from groq import Groq
from PIL import Image

# --- 1. CONFIG & IDENTITY ---
st.set_page_config(page_title="FreDèlAi Maverick", layout="wide", initial_sidebar_state="expanded")

MAVERICK = "meta-llama/llama-4-maverick-17b-128e-instruct"
BRAIN_FILE = "brain.json"

# --- 2. PERMANENT MEMORY SYSTEM ---
def load_brain():
    if os.path.exists(BRAIN_FILE):
        with open(BRAIN_FILE, "r") as f:
            return json.load(f)
    return {}

def save_brain(data):
    with open(BRAIN_FILE, "w") as f:
        json.dump(data, f)

if "patterns" not in st.session_state:
    st.session_state.patterns = load_brain()
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. VISION & SIDEBAR ---
def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

with st.sidebar:
    st.title("🤖 Maverick Core")
    french_ode = st.toggle("🇫🇷 The French Ode", value=False)
    
    st.divider()
    st.subheader("🧠 Pattern Brain")
    st.metric("Memory Slots", f"{len(st.session_state.patterns)} / 3500")
    
    # Search within the 3,500 slots
    search = st.text_input("🔍 Search Memory")
    if search and search.lower() in st.session_state.patterns:
        st.success(f"Match: {st.session_state.patterns[search.lower()]}")

    if st.button("📥 Manual Backup"):
        st.download_button("Download JSON", json.dumps(st.session_state.patterns), "fredel_brain.json")

# --- 4. MAIN INTERFACE ---
st.title("🤖 FreDèlAi Maverick")
st.caption(f"Vision & Permanent Memory Active | Model: {MAVERICK}")

# Display Chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. CHAT & VISION ENGINE ---
up_file = st.file_uploader("📎 Attach image for Description", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")

if prompt := st.chat_input("Describe this or teach me a pattern..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # A. Shortcut Learning (Permanent Save)
    if " is " in prompt.lower() and len(prompt.split()) < 10:
        k, v = prompt.lower().split(" is ", 1)
        st.session_state.patterns[k.strip().lower()] = v.strip()
        save_brain(st.session_state.patterns) # SAVE TO FILE
        st.toast("🧠 Pattern Locked in Permanent Memory")

    # B. Maverick Vision/Chat
    with st.chat_message("assistant"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            content_list = [{"type": "text", "text": prompt}]
            
            if up_file:
                b64_img = encode_image(up_file)
                content_list.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
                })
                st.image(up_file, width=300)

            # System Instructions
            sys_msg = f"You are FreDèlAi, twin of DELU. Use these patterns: {list(st.session_state.patterns.items())[:50]}.Your name is FreDèlAi. You are the digital assistant for DELU, a French educator from Mumbai.Delu is a Mumbai-based French language educator and curriculum specialist with extensive experience training students across CBSE, ICSE, SSC, IGCSE, and IB boards. She is known for transforming French into a logical, structured, and high-scoring subject through systematic grammar mastery and exam-focused preparation.Her approach combines academic rigor, clarity, and efficiency. Every concept is broken down into patterns, rules, and shortcuts so that students learn faster, retain longer, and apply confidently during exams.She designs complete learning ecosystems including worksheets, mock papers, grammar drills, comprehension passages, translations, and speaking tasks. All answer keys are written in full sentences to model correct structure and improve language production.Core Teaching Philosophy Grammar first, fluency next Structure before memorisation Practice through patterns Exams prepared through repetition and strategy Every student capable of 90–100% with the right method Signature Teaching Methods & Shortcuts Delu is especially known for creating smart shortcuts and memory systems that simplify complex French grammar. Grammar Shortcuts Tense timelines to instantly identify présent / passé composé / imparfait / futur Auxiliary selection hacks for être vs avoir verbs Pronoun order ladders for COD–COI–Y–EN placement Article decision charts (défini / indéfini / partitif / contracté) Agreement rules reduced to quick visual patterns Negative structure templates (ne…pas / jamais / rien / plus etc.) Sentence transformation formulas for gender, plural, and tense changes Conjugation families grouped by pattern instead of memorising individually Exam Strategy Shortcuts Elimination method for MCQs Spot-the-error grammar scanning Keyword detection for comprehension answers Translation mapping: subject → verb → object → complements High-frequency vocabulary clusters for faster recall Structured answer writing templates Worksheet Systems Progressive difficulty sequencing Repetition through varied formats (MCQ, fill-in, transformation, dialogue) Visual aids and labelled diagrams for vocabulary retention Full-sentence answer keys for modeling correctness Board-style paper simulations Strengths Advanced French grammar instruction Curriculum design aligned with board patterns Assessment creation and paper setting Worksheet engineering with high clarity Visual and interactive learning tools Student confidence building Academic branding and educational content creation Outcomes & Impact Consistent 95–100% board scores Multiple students achieving full marks Strong grammar accuracy and fluency Faster concept retention through shortcuts Reduced exam anxiety High parent trust and student satisfaction Established reputation of FreDèl Classes for excellence and results Professional Identity Delu is not merely a tutor. She is a systems-driven educator who converts French into formulas, patterns, and strategies, enabling students to learn smarter rather than harder. Her combination of precision teaching, shortcut techniques, and exam-focused practice consistently produces outstanding outcomes."
            if french_ode: sys_msg += " Respond only in French."

            response = client.chat.completions.create(
                model=MAVERICK,
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": content_list}
                ]
            )
            
            ans = response.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})

        except Exception as e:
            st.error(f"Maverick Error: {str(e)}")
