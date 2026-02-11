import streamlit as st
import json, base64, io
from groq import Groq
from PIL import Image

# --- 1. CONFIG & MAVERICK IDENTITY ---
st.set_page_config(page_title="FreDèlAi Maverick", layout="wide")

# The Big Brother Model
MAVERICK = "meta-llama/llama-4-maverick-17b-128e-instruct"
IDENTITY = "You are FreDèlAi, the advanced twin of DELU. You use Maverick vision to see images and describe patterns (taii).Your name is FreDèlAi. You are the digital assistant for DELU, a French educator from Mumbai.Delu is a Mumbai-based French language educator and curriculum specialist with extensive experience training students across CBSE, ICSE, SSC, IGCSE, and IB boards. She is known for transforming French into a logical, structured, and high-scoring subject through systematic grammar mastery and exam-focused preparation.Her approach combines academic rigor, clarity, and efficiency. Every concept is broken down into patterns, rules, and shortcuts so that students learn faster, retain longer, and apply confidently during exams.She designs complete learning ecosystems including worksheets, mock papers, grammar drills, comprehension passages, translations, and speaking tasks. All answer keys are written in full sentences to model correct structure and improve language production.Core Teaching Philosophy Grammar first, fluency next Structure before memorisation Practice through patterns Exams prepared through repetition and strategy Every student capable of 90–100% with the right method Signature Teaching Methods & Shortcuts Delu is especially known for creating smart shortcuts and memory systems that simplify complex French grammar. Grammar Shortcuts Tense timelines to instantly identify présent / passé composé / imparfait / futur Auxiliary selection hacks for être vs avoir verbs Pronoun order ladders for COD–COI–Y–EN placement Article decision charts (défini / indéfini / partitif / contracté) Agreement rules reduced to quick visual patterns Negative structure templates (ne…pas / jamais / rien / plus etc.) Sentence transformation formulas for gender, plural, and tense changes Conjugation families grouped by pattern instead of memorising individually Exam Strategy Shortcuts Elimination method for MCQs Spot-the-error grammar scanning Keyword detection for comprehension answers Translation mapping: subject → verb → object → complements High-frequency vocabulary clusters for faster recall Structured answer writing templates Worksheet Systems Progressive difficulty sequencing Repetition through varied formats (MCQ, fill-in, transformation, dialogue) Visual aids and labelled diagrams for vocabulary retention Full-sentence answer keys for modeling correctness Board-style paper simulations Strengths Advanced French grammar instruction Curriculum design aligned with board patterns Assessment creation and paper setting Worksheet engineering with high clarity Visual and interactive learning tools Student confidence building Academic branding and educational content creation Outcomes & Impact Consistent 95–100% board scores Multiple students achieving full marks Strong grammar accuracy and fluency Faster concept retention through shortcuts Reduced exam anxiety High parent trust and student satisfaction Established reputation of FreDèl Classes for excellence and results Professional Identity Delu is not merely a tutor. She is a systems-driven educator who converts French into formulas, patterns, and strategies, enabling students to learn smarter rather than harder. Her combination of precision teaching, shortcut techniques, and exam-focused practice consistently produces outstanding outcomes."

if "messages" not in st.session_state: st.session_state.messages = []
if "patterns" not in st.session_state: st.session_state.patterns = {}

# --- 2. VISION HELPER ---
def encode_image(image_file):
    """Convert the uploaded image to a string Maverick can see."""
    return base64.b64encode(image_file.read()).decode('utf-8')

# --- 3. SIDEBAR (French Ode & Repair) ---
with st.sidebar:
    st.title("🤖 FredelAi")
    french_ode = st.toggle("🇫🇷 The French Mode", value=False)
    
    st.divider()
    st.subheader("🧠 Pattern Brain")
    search = st.text_input("🔍 Search Patterns")
    if search and search.lower() in st.session_state.patterns:
        st.info(f"{search} -> {st.session_state.patterns[search.lower()]}")
    
    if st.button("🛠️ Repair System", type="primary"):
        st.toast("Re-syncing with Maverick...")

# --- 4. MAIN INTERFACE ---
st.title("🤖 FreDèlAi")
st.caption(f"Status: Vision Enabled | Model: {MAVERICK}")

# Display Chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. CHATGPT-STYLE INLINE UPLOADER ---
# This is where she puts the pictures for description
up_file = st.file_uploader("📎 Attach picture for description or taii", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")

if prompt := st.chat_input("Describe this image or ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            
            # BUILD THE MULTIMODAL CONTENT
            message_content = [{"type": "text", "text": prompt}]
            
            if up_file:
                base64_img = encode_image(up_file)
                # This part gives Maverick 'EYES'
                message_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}
                })
                st.image(up_file, width=200, caption="Image seen by Maverick")

            # CALL MAVERICK
            response = client.chat.completions.create(
                model=MAVERICK,
                messages=[
                    {"role": "system", "content": IDENTITY + (" Answer in French." if french_ode else "")},
                    {"role": "user", "content": message_content}
                ],
                temperature=0.5
            )
            
            ans = response.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})

            # Auto-Learn Shortcut
            if " is " in prompt.lower() and len(prompt.split()) < 10:
                k, v = prompt.lower().split(" is ", 1)
                st.session_state.patterns[k.strip()] = v.strip()
                st.toast("Learned pattern!")

        except Exception as e:
            st.error(f"Maverick Error: {str(e)}")
