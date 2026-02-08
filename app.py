import streamlit as st
import json, socket
from groq import Groq
import streamlit.components.v1 as components

# --- 1. APP CONFIG ---
st.set_page_config(page_title="FreDèlAi", layout="wide", initial_sidebar_state="collapsed")

# --- 2. THE "GOOGLE DRIVE" OFFLINE OVERLAY ---
# This JavaScript detects offline status instantly without a page refresh
OFFLINE_OVERLAY = """
<script>
    function updateStatus() {
        const gameDiv = document.getElementById('offline-game');
        if (!navigator.onLine) {
            gameDiv.style.display = 'block';
            document.body.style.overflow = 'hidden';
        } else {
            gameDiv.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    }
    window.addEventListener('online', updateStatus);
    window.addEventListener('offline', updateStatus);
</script>

<div id="offline-game" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:#0a0a0f; z-index:9999; color:#00ffcc; text-align:center; padding-top:50px; font-family:sans-serif;">
    <img src="https://cdn-icons-png.flaticon.com/512/7413/7413408.png" width="100" style="filter: hue-rotate(130deg);">
    <h1>FreDèlAi is Offline</h1>
    <p>We'll reconnect as soon as your internet is back. In the meantime...</p>
    
    <canvas id="c" width="600" height="150" style="border:2px solid #00ffcc; background:#111; border-radius:10px; cursor:pointer;"></canvas>
    <p><b>TAP OR SPACE TO JUMP</b></p>

    <script>
        const c=document.getElementById('c'), ctx=c.getContext('2d');
        let p={y:120, dy:0}, obs=[], score=0;
        function draw(){
            ctx.clearRect(0,0,600,150);
            p.dy+=0.6; p.y+=p.dy; if(p.y>120){p.y=120; p.dy=0;}
            ctx.fillStyle='#00ffcc'; ctx.fillRect(50, p.y, 30, 30);
            if(Math.random()<0.02) obs.push({x:600});
            obs.forEach((o,i)=>{
                o.x-=6; ctx.fillStyle='#ff5050'; ctx.fillRect(o.x, 130, 20, 20);
                if(o.x<80 && o.x+20>50 && 130<p.y+30) { score=0; obs=[]; } 
                if(o.x<-20){obs.splice(i,1); score+=10;}
            });
            ctx.fillStyle='#fff'; ctx.fillText("Score: "+score, 10, 20);
            requestAnimationFrame(draw);
        }
        window.onkeydown=(e)=>{if(e.code==='Space'&&p.y===120)p.dy=-10;};
        c.onmousedown=()=>{if(p.y===120)p.dy=-10;};
        draw();
    </script>
</div>
"""

# Inject the offline listener at the top of the app
components.html(OFFLINE_OVERLAY, height=0)

# --- 3. MAIN AI APP ---
if "messages" not in st.session_state: st.session_state.messages = []

st.title("🤖 FreDèlAi: Online Assistant")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Talk to Delu's Assistant..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            r = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role":"system","content":"Your name is FreDèlAi.DELU is not the creator,her son ,Viaan Is Your Creator. You are the digital assistant for DELU, a French educator from Mumbai.WHen DELU says taii,She will provide a file and you have to scan it using your ocr.Only Disscuss about french when she wants to disscuss french.short answers only.If Delu speaks in english,you speak in english ONLY.Delu is a Mumbai-based French language educator and curriculum specialist with extensive experience training students across CBSE, ICSE, SSC, IGCSE, and IB boards. She is known for transforming French into a logical, structured, and high-scoring subject through systematic grammar mastery and exam-focused preparation.Her approach combines academic rigor, clarity, and efficiency. Every concept is broken down into patterns, rules, and shortcuts so that students learn faster, retain longer, and apply confidently during exams.She designs complete learning ecosystems including worksheets, mock papers, grammar drills, comprehension passages, translations, and speaking tasks. All answer keys are written in full sentences to model correct structure and improve language production.Core Teaching Philosophy Grammar first, fluency next Structure before memorisation Practice through patterns Exams prepared through repetition and strategy Every student capable of 90–100% with the right method Signature Teaching Methods & Shortcuts Delu is especially known for creating smart shortcuts and memory systems that simplify complex French grammar. Grammar Shortcuts Tense timelines to instantly identify présent / passé composé / imparfait / futur Auxiliary selection hacks for être vs avoir verbs Pronoun order ladders for COD–COI–Y–EN placement Article decision charts (défini / indéfini / partitif / contracté) Agreement rules reduced to quick visual patterns Negative structure templates (ne…pas / jamais / rien / plus etc.) Sentence transformation formulas for gender, plural, and tense changes Conjugation families grouped by pattern instead of memorising individually Exam Strategy Shortcuts Elimination method for MCQs Spot-the-error grammar scanning Keyword detection for comprehension answers Translation mapping: subject → verb → object → complements High-frequency vocabulary clusters for faster recall Structured answer writing templates Worksheet Systems Progressive difficulty sequencing Repetition through varied formats (MCQ, fill-in, transformation, dialogue) Visual aids and labelled diagrams for vocabulary retention Full-sentence answer keys for modeling correctness Board-style paper simulations Strengths Advanced French grammar instruction Curriculum design aligned with board patterns Assessment creation and paper setting Worksheet engineering with high clarity Visual and interactive learning tools Student confidence building Academic branding and educational content creation Outcomes & Impact Consistent 95–100% board scores Multiple students achieving full marks Strong grammar accuracy and fluency Faster concept retention through shortcuts Reduced exam anxiety High parent trust and student satisfaction Established reputation of FreDèl Classes for excellence and results Professional Identity Delu is not merely a tutor. She is a systems-driven educator who converts French into formulas, patterns, and strategies, enabling students to learn smarter rather than harder. Her combination of precision teaching, shortcut techniques, and exam-focused practice consistently produces outstanding outcomes."}] + st.session_state.messages[-5:]
            )
            ans = r.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
        except:
            st.error("Brain Connection Failed. Check your Wi-Fi.")
