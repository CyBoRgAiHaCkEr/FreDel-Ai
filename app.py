import streamlit as st
import json, socket
from groq import Groq
import streamlit.components.v1 as components

# --- 1. CONFIG & MEMORY ---
st.set_page_config(page_title="FreDèlAi", layout="wide")

if "patterns" not in st.session_state: st.session_state.patterns = {}
if "messages" not in st.session_state: st.session_state.messages = []

# --- 2. IDENTITY (The Brain) ---
IDENTITY = (
    "You are FreDèlAi, the digital assistant created by DELU, "
    "an expert French teacher from Mumbai. Delu is your creator and the boss. "
    "Focus on French patterns and be professional."
)

# --- 3. THE NO-DINO DIAGNOSTIC GAME ---
def check_connection():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except: return False

# Built-in JavaScript game for Offline Mode
OFFLINE_GAME = """
<div style="color: #00ffcc; background: #0a0a0f; border: 2px solid #00ffcc; padding: 20px; border-radius: 15px; text-align: center; font-family: monospace;">
    <h3>📴 DIAGNOSTIC: CONNECTION LOST</h3>
    <canvas id="c" width="600" height="150" style="background: #111; border-radius: 5px; cursor: pointer;"></canvas>
    <p><b>JUMP OVER THE GLITCHES</b><br>(Space or Click to Jump)</p>
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

# --- 4. MAIN INTERFACE ---
online = check_connection()

with st.sidebar:
    st.title("🤖 FreDèlAi")
    st.write(f"🧠 Memory: {len(st.session_state.patterns)}/3500")
    if not online: st.error("Offline Mode")
    if st.button("📥 Export Brain"):
        st.download_button("Download", json.dumps(st.session_state.patterns), "brain.json")

# --- 5. CHAT ENGINE ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Message..."):
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
    
    # AI CHAT WITH GAME FALLBACK
    else:
        with st.chat_message("assistant"):
            if online:
                try:
                    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                    r = client.chat.completions.create(
                        model="openai/gpt-oss-120b",
                        messages=[{"role":"system","content":IDENTITY}] + st.session_state.messages[-5:],
                        timeout=8
                    )
                    ans = r.choices[0].message.content
                    st.markdown(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                except:
                    st.error("⚠️ AI TIMEOUT")
                    components.html(OFFLINE_GAME, height=350)
            else:
                st.warning("⚠️ OFFLINE")
                components.html(OFFLINE_GAME, height=350)
