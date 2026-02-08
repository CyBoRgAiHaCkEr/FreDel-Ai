import streamlit as st
import json, socket, random
from groq import Groq
import streamlit.components.v1 as components

# --- 1. SETTINGS ---
st.set_page_config(page_title="FreDèlAi", layout="wide", initial_sidebar_state="expanded")

if "patterns" not in st.session_state: st.session_state.patterns = {}
if "messages" not in st.session_state: st.session_state.messages = []

# --- 2. NEW GAME: GLITCH-SHOOTER (No Jumping) ---
# Use WASD or Arrows to move, Space to shoot Glitches.
SHOOTER_GAME = """
<div style="color:#00ffcc; background:#0a0a0f; padding:20px; border:2px solid #00ffcc; border-radius:15px; text-align:center; font-family:monospace;">
    <h3>🚀 EMERGENCY PROTOCOL</h3>
    <p>Move: Arrows/WASD | Shoot: Space</p>
    <canvas id="g" width="600" height="300" style="background:#000; border:1px solid #333;"></canvas>
    <script>
        const c=document.getElementById('g'), x=c.getContext('2d');
        let p={x:300, y:270}, bullets=[], enemies=[], score=0;
        function loop(){
            x.clearRect(0,0,600,300);
            x.fillStyle='#00ffcc'; x.fillRect(p.x, p.y, 20, 20); // Player
            if(Math.random()<0.05) enemies.push({x:Math.random()*580, y:0});
            bullets.forEach((b,bi)=>{
                b.y-=7; x.fillStyle='#fff'; x.fillRect(b.x, b.y, 4, 10);
                if(b.y<0) bullets.splice(bi,1);
            });
            enemies.forEach((e,ei)=>{
                e.y+=2; x.fillStyle='#ff5050'; x.fillText("GLITCH", e.x, e.y);
                bullets.forEach((b,bi)=>{
                    if(b.x>e.x && b.x<e.x+40 && b.y>e.y-10 && b.y<e.y+10){
                        enemies.splice(ei,1); bullets.splice(bi,1); score+=10;
                    }
                });
                if(e.y>300) { enemies.splice(ei,1); score-=5; }
            });
            x.fillStyle='#00ffcc'; x.fillText("STABILITY: "+score+"%", 10, 20);
            requestAnimationFrame(loop);
        }
        window.onkeydown=(e)=>{
            if(e.key==='ArrowLeft'||e.key==='a') p.x-=15;
            if(e.key==='ArrowRight'||e.key==='d') p.x+=15;
            if(e.key===' ') bullets.push({x:p.x+8, y:p.y});
        };
        loop();
    </script>
</div>
"""

# --- 3. SYSTEM REPAIR LOGIC ---
def run_repair():
    """Attempt to fix connection and clear model errors."""
    with st.spinner("🔧 Running System Diagnostic & Repair..."):
        try:
            # Check Internet
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            # Try a tiny "Handshake" call to Groq
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            client.models.list()
            st.success("✅ Brain Connection Restored! You can chat now.")
            return True
        except:
            st.error("❌ Repair Failed: Network is physically disconnected.")
            return False

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🤖 FreDèlAi Core")
    
    # THE REPAIR/PANIC BUTTON
    if st.button("🛠️ PANIC: REPAIR SYSTEM", type="primary", use_container_width=True):
        if not run_repair():
            st.session_state.show_game = True
        else:
            st.session_state.show_game = False

    st.divider()
    
    # SEARCH BAR
    search = st.text_input("🔍 Search Memory", placeholder="Search patterns...")
    if search:
        res = st.session_state.patterns.get(search.lower())
        if res: st.code(f"{search} -> {res}")
    
    st.metric("Stored Patterns", len(st.session_state.patterns))
    st.download_button("📥 Export Brain", json.dumps(st.session_state.patterns), "brain.json")

# --- 5. CHAT ENGINE ---
st.title("🤖 FreDèlAi Online")

# If system is broken, show Shooter Game
if st.session_state.get("show_game"):
    components.html(SHOOTER_GAME, height=450)
    if st.button("Try Reconnecting Again"):
        st.session_state.show_game = not run_repair()
        st.rerun()

# Main Chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # Shortcut logic
    if " is " in prompt.lower() and len(prompt.split()) < 10:
        k, v = prompt.lower().split(" is ", 1)
        st.session_state.patterns[k.strip().lower()] = v.strip()
        st.toast("Learned!")
    elif (res := st.session_state.patterns.get(prompt.lower().strip())):
        with st.chat_message("assistant"): st.markdown(res)
        st.session_state.messages.append({"role": "assistant", "content": res})
    else:
        # AI Logic
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
                st.warning("⚠️ Connection Glitch! Use the Repair Button in the sidebar.")
