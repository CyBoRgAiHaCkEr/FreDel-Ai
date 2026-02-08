import streamlit as st
import json, socket
from groq import Groq
import streamlit.components.v1 as components

# --- 1. SETTINGS ---
st.set_page_config(page_title="FreDèlAi", layout="wide", initial_sidebar_state="expanded")

if "patterns" not in st.session_state: st.session_state.patterns = {}
if "messages" not in st.session_state: st.session_state.messages = []
if "panic" not in st.session_state: st.session_state.panic = False

# --- 2. THE GAME CODE ---
GAME_CODE = """
<div style="color:#00ffcc; background:#0a0a0f; padding:20px; border:2px solid #ff5050; border-radius:15px; text-align:center; font-family:monospace;">
    <h2 style="color:#ff5050;">🚨 PANIC MODE: CYBER-RUNNER</h2>
    <canvas id="g" width="600" height="150" style="background:#111; border-radius:5px;"></canvas>
    <script>
        const c=document.getElementById('g'), x=c.getContext('2d');
        let p={y:120, dy:0}, obs=[];
        function loop(){
            x.clearRect(0,0,600,150);
            p.dy+=0.6; p.y+=p.dy; if(p.y>120){p.y=120; p.dy=0;}
            x.fillStyle='#00ffcc'; x.fillRect(50, p.y, 30, 30);
            if(Math.random()<0.02) obs.push({x:600});
            obs.forEach((o,i)=>{
                o.x-=7; x.fillStyle='#ff5050'; x.fillRect(o.x, 130, 20, 20);
                if(o.x<80 && o.x+20>50 && 130<p.y+30) obs=[];
                if(o.x<-20) obs.splice(i,1);
            });
            requestAnimationFrame(loop);
        }
        window.onkeydown=(e)=>{if(e.code==='Space'&&p.y===120)p.dy=-10;};
        loop();
    </script>
</div>
"""

# --- 3. SIDEBAR (CONTROLS & SEARCH) ---
with st.sidebar:
    st.title("🤖 FreDèlAi Core")
    
    # PANIC BUTTON
    if st.button("🚨 PANIC BUTTON", use_container_width=True, type="primary"):
        st.session_state.panic = not st.session_state.panic
    
    st.divider()
    
    # SEARCH & MEMORY
    st.subheader("🧠 Pattern Brain")
    search_query = st.text_input("🔍 Search Patterns", placeholder="e.g. taii")
    if search_query:
        match = st.session_state.patterns.get(search_query.lower())
        if match: st.success(f"Result: {match}")
        else: st.info("Pattern not found.")
    
    st.metric("Total Patterns", f"{len(st.session_state.patterns)} / 3500")
    
    # DATA SYNC
    st.download_button("📥 Export Brain", json.dumps(st.session_state.patterns), "brain.json", use_container_width=True)
    up = st.file_uploader("📤 Sync Brain", type="json")
    if up:
        st.session_state.patterns = json.load(up)
        st.rerun()

# --- 4. MAIN INTERFACE ---
st.title("🤖 FreDèlAi Assistant")

if st.session_state.panic:
    st.warning("Panic Mode Active. AI systems paused.")
    components.html(GAME_CODE, height=400)
    if st.button("Exit Panic Mode"):
        st.session_state.panic = False
        st.rerun()
else:
    # CHAT LOGIC
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Ask Delu's Assistant..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        # 1. Shortcut logic
        if " is " in prompt.lower() and len(prompt.split()) < 15:
            k, v = prompt.lower().split(" is ", 1)
            st.session_state.patterns[k.strip().lower()] = v.strip()
            st.toast("Pattern Learned!")
        elif prompt.lower().strip() in st.session_state.patterns:
            res = st.session_state.patterns[prompt.lower().strip()]
            st.session_state.messages.append({"role": "assistant", "content": res})
            st.rerun()
        else:
            # 2. AI Call
            with st.chat_message("assistant"):
                try:
                    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                    r = client.chat.completions.create(
                        model="openai/gpt-oss-120b",
                        messages=[{"role":"system","content":"Assistant to DELU."}] + st.session_state.messages[-5:]
                    )
                    ans = r.choices[0].message.content
                    st.markdown(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                except:
                    st.error("Connection Failed. Entering Panic Mode...")
                    st.session_state.panic = True
                    st.rerun()
