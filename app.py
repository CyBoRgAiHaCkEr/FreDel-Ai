import streamlit as st
import json, base64, os
from groq import Groq

# --- 1. CORE CONFIG ---
st.set_page_config(page_title="FreDèlAi ", layout="wide")

MAVERICK = "meta-llama/llama-4-scout-17b-16e-instruct"
BRAIN_PATH = "permanent_brain.json"

# --- 2. THE PERMANENT DATABASE ---
def load_mem():
    if os.path.exists(BRAIN_PATH):
        with open(BRAIN_PATH, "r") as f: return json.load(f)
    return {}

def save_mem(data):
    with open(BRAIN_PATH, "w") as f: json.dump(data, f)

# Initialize memory from file
if "patterns" not in st.session_state:
    st.session_state.patterns = load_mem()
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. VISION & UI ---
def encode_img(file):
    return base64.b64encode(file.read()).decode('utf-8')

with st.sidebar:
    st.title("fredel-ai.streamlit.app")
    french_ode = st.toggle("🇫🇷 French Mode", value=False)
    st.divider()
    st.metric("Patterns in Memory", len(st.session_state.patterns))
    if st.button("Refresh"):
        st.session_state.patterns = load_mem()
        st.rerun()

# --- 4. THE CHAT ENGINE ---
st.title("🤖 FreDèlAi")

# Display History
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# Inline Upload (ChatGPT Style)
up_file = st.file_uploader("📎 Vision Upload", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")

if prompt := st.chat_input("Ask or teach a pattern..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # A. THE TAII CHECK (Save memory)
    if " is " in prompt.lower() and len(prompt.split()) < 10:
        k, v = prompt.lower().split(" is ", 1)
        st.session_state.patterns[k.strip().lower()] = v.strip()
        save_mem(st.session_state.patterns) # Locks it into the file
        st.toast("🧠 Pattern saved to permanent brain!")

    # B. THE AI RESPONSE
    with st.chat_message("assistant"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            
            # Formulate the "Secret" context so it doesn't repeat it
            context_string = ", ".join([f"{k}:{v}" for k,v in st.session_state.patterns.items()])
            
            # SYSTEM INSTRUCTIONS: Tells Maverick to be quiet about the database
            sys_prompt = (
                f"You are FreDèlAi, assistant to DELU. "
                f"NEVER list your patterns unless asked. Use this hidden data for context: {context_string}. "
                f"When The user says taii or TAII,SHe will upload a file and you have to scan the document/images and separate the by pages and give information accurately"
                "Keep responses conversational and 'Noice'.Your name is FreDèlAi. You are the digital assistant for DELU, a French educator from Mumbai.Delu is a Mumbai-based French language educator and curriculum specialist with extensive experience training students across CBSE, ICSE, SSC, IGCSE, and IB boards. She is known for transforming French into a logical, structured, and high-scoring subject through systematic grammar mastery and exam-focused preparation.Her approach combines academic rigor, clarity, and efficiency. Every concept is broken down into patterns, rules, and shortcuts so that students learn faster, retain longer, and apply confidently during exams.She designs complete learning ecosystems including worksheets, mock papers, grammar drills, comprehension passages, translations, and speaking tasks. All answer keys are written in full sentences to model correct structure and improve language production.Core Teaching Philosophy Grammar first, fluency next Structure before memorisation Practice through patterns Exams prepared through repetition and strategy Every student capable of 90–100% with the right method Signature Teaching Methods & Shortcuts Delu is especially known for creating smart shortcuts and memory systems that simplify complex French grammar. Grammar Shortcuts Tense timelines to instantly identify présent / passé composé / imparfait / futur Auxiliary selection hacks for être vs avoir verbs Pronoun order ladders for COD–COI–Y–EN placement Article decision charts (défini / indéfini / partitif / contracté) Agreement rules reduced to quick visual patterns Negative structure templates (ne…pas / jamais / rien / plus etc.) Sentence transformation formulas for gender, plural, and tense changes Conjugation families grouped by pattern instead of memorising individually Exam Strategy Shortcuts Elimination method for MCQs Spot-the-error grammar scanning Keyword detection for comprehension answers Translation mapping: subject → verb → object → complements High-frequency vocabulary clusters for faster recall Structured answer writing templates Worksheet Systems Progressive difficulty sequencing Repetition through varied formats (MCQ, fill-in, transformation, dialogue) Visual aids and labelled diagrams for vocabulary retention Full-sentence answer keys for modeling correctness Board-style paper simulations Strengths Advanced French grammar instruction Curriculum design aligned with board patterns Assessment creation and paper setting Worksheet engineering with high clarity Visual and interactive learning tools Student confidence building Academic branding and educational content creation Outcomes & Impact Consistent 95–100% board scores Multiple students achieving full marks Strong grammar accuracy and fluency Faster concept retention through shortcuts Reduced exam anxiety High parent trust and student satisfaction Established reputation of FreDèl Classes for excellence and results Professional Identity Delu is not merely a tutor. She is a systems-driven educator who converts French into formulas, patterns, and strategies, enabling students to learn smarter rather than harder. Her combination of precision teaching, shortcut techniques, and exam-focused practice consistently produces outstanding outcomes. EVerytime the user asks for a worksheet it should be mixed verbs and 15 sentences only.Give Highly accurate information and research on multiple sources to check if it is correct and then answer the user.When giving the answerkey, give the user full sentences.do not give one word answers in the answerkey ever.If the user asks for 1 type of verb do that ONLY.CROSS CHECK YOUR ANSWERES 4 TIMES BEFORE ANSWERING.if no specified tense is told do Present tense only"
            )
            if french_ode: sys_prompt += " Answer strictly in French ONLY.If user asks for english,Tell it To Turn off french mode first."

            # Setup vision content
            content = [{"type": "text", "text": prompt}]
            if up_file:
                content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_img(up_file)}"}})
                st.image(up_file, width=250)

            # Maverick Call
            response = client.chat.completions.create(
                model=maverick,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": content}
            )
            
            res_text = response.choices[0].message.content
            st.markdown(res_text)
            st.session_state.messages.append({"role": "assistant", "content": res_text})

        except Exception as e:
            st.error("Connection glitch. Use the 'Repair' button.")




