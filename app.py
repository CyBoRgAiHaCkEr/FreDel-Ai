import streamlit as st
import json, socket, time
from groq import Groq
import streamlit.components.v1 as components

# --- 1. CONFIG & MEMORY ---
st.set_page_config(page_title="FreDèlAi", layout="wide")

if "patterns" not in st.session_state: st.session_state.patterns = {}
if "messages" not in st.session_state: st.session_state.messages = []

# --- 2. IDENTITY (The Brain) ---
IDENTITY = (
    "Your name is FreDèlAi.DELU is not the creator,her son ,Viaan Is Your Creator. You are the digital assistant for DELU, a French educator from Mumbai.WHen DELU says taii,She will provide a file and you have to scan it using your ocr.Only Disscuss about french when she wants to disscuss french.short answers only.If Delu speaks in english,you speak in english ONLY.Delu is a Mumbai-based French language educator and curriculum specialist with extensive experience training students across CBSE, ICSE, SSC, IGCSE, and IB boards. She is known for transforming French into a logical, structured, and high-scoring subject through systematic grammar mastery and exam-focused preparation.Her approach combines academic rigor, clarity, and efficiency. Every concept is broken down into patterns, rules, and shortcuts so that students learn faster, retain longer, and apply confidently during exams.She designs complete learning ecosystems including worksheets, mock papers, grammar drills, comprehension passages, translations, and speaking tasks. All answer keys are written in full sentences to model correct structure and improve language production.Core Teaching Philosophy Grammar first, fluency next Structure before memorisation Practice through patterns Exams prepared through repetition and strategy Every student capable of 90–100% with the right method Signature Teaching Methods & Shortcuts Delu is especially known for creating smart shortcuts and memory systems that simplify complex French grammar. Grammar Shortcuts Tense timelines to instantly identify présent / passé composé / imparfait / futur Auxiliary selection hacks for être vs avoir verbs Pronoun order ladders for COD–COI–Y–EN placement Article decision charts (défini / indéfini / partitif / contracté) Agreement rules reduced to quick visual patterns Negative structure templates (ne…pas / jamais / rien / plus etc.) Sentence transformation formulas for gender, plural, and tense changes Conjugation families grouped by pattern instead of memorising individually Exam Strategy Shortcuts Elimination method for MCQs Spot-the-error grammar scanning Keyword detection for comprehension answers Translation mapping: subject → verb → object → complements High-frequency vocabulary clusters for faster recall Structured answer writing templates Worksheet Systems Progressive difficulty sequencing Repetition through varied formats (MCQ, fill-in, transformation, dialogue) Visual aids and labelled diagrams for vocabulary retention Full-sentence answer keys for modeling correctness Board-style paper simulations Strengths Advanced French grammar instruction Curriculum design aligned with board patterns Assessment creation and paper setting Worksheet engineering with high clarity Visual and interactive learning tools Student confidence building Academic branding and educational content creation Outcomes & Impact Consistent 95–100% board scores Multiple students achieving full marks Strong grammar accuracy and fluency Faster concept retention through shortcuts Reduced exam anxiety High parent trust and student satisfaction Established reputation of FreDèl Classes for excellence and results Professional Identity Delu is not merely a tutor. She is a systems-driven educator who converts French into formulas, patterns, and strategies, enabling students to learn smarter rather than harder. Her combination of precision teaching, shortcut techniques, and exam-focused practice consistently produces outstanding outcomes."
)

# --- 3. DIAGNOSTIC ENGINE (No-Dino Mode) ---
def is_online():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except: return False

# This JavaScript game runs IN THE BROWSER (True Offline)
JS_GAME = """
<div style="color: #00ffcc; background: #0a0a0f; text-align: center; border: 2px solid #00ffcc; padding: 20px; border-radius: 15px; font-family: monospace;">
    <h3>📴 DIAGNOSTIC: BRAIN DISCONNECTED</h3>
    <canvas id="g" width="600" height="150" style="background: #111; border-radius: 5px;"></canvas>
    <p>Jump over the Glitches! (Space/Click)</p>
    <script>
        const c=document.getElementById('g'), x=c.getContext('2d');
        let p={y:120, dy:0}, obs=[], score=0;
        function draw(){
            x.clearRect(0,0,600,150); x.fillStyle='#00ffcc';
            p.dy+=0.6; p.y+=p.dy; if(p.y>120){p.y=120; p.dy=0;}
            x.fillRect(50, p.y, 30, 30);
            if(Math.random()<0.02) obs.push({x:600});
            obs.forEach((o,i)=>{
                o.x-=6; x.fillStyle='#ff5050'; x.fillRect(o.x, 130, 20, 20);
                if(o.x<80 && o.x+20>50 && 130<p.y+30) score=0; 
                if(o.x<-20){obs.splice(i,1); score+=10;}
            });
            requestAnimationFrame(draw);
        }
        window.onkeydown=(e)=>{if(e.code==='Space'&&p.y===120)p.dy=-10;};
        c.onmousedown=()=>{if(p.y===120)p.dy=-10;};
        draw();
    </script>
</div>
"""

# --- 4. THE INTERFACE ---
with st.sidebar:
    st.title("🤖 FreDèlAi Control")
    st.write(f"🧠 Pattern Memory: {len(st.session_state.patterns)} / 3500")
    if st.button("📥 Export Brain"):
        st.download_button("Download JSON", json.dumps(st.session_state.patterns), "delu_brain.json")

# --- 5. CHAT ENGINE (With Fix-or-Game Logic) ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Ask Delu's Assistant..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # SHORTCUT CHECK (taii is...)
    if " is " in prompt.lower() and len(prompt.split()) < 20:
        k, v = prompt.lower().split(" is ", 1)
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast("Learned!")
    elif prompt.lower().strip() in st.session_state.patterns:
        res = st.session_state.patterns[prompt.lower().strip()]
        with st.chat_message("assistant"): st.markdown(res)
    
    # AI CHAT WITH DIAGNOSTIC FALLBACK
    else:
        with st.chat_message("assistant"):
            if is_online():
                try:
                    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                    r = client.chat.completions.create(
                        model="openai/gpt-oss-120b",
                        messages=[{"role":"system","content":IDENTITY}] + st.session_state.messages[-6:],
                        timeout=8
                    )
                    ans = r.choices[0].message.content
                    st.markdown(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                except:
                    st.error("Model Error. Try again or check API.")
                    components.html(JS_GAME, height=300)
            else:
                st.error("No Internet Connection Found.")
                components.html(JS_GAME, height=300)
