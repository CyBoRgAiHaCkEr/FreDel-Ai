import streamlit as st
import os, json, subprocess, sys, socket, numpy as np
import pdfplumber, easyocr, cv2
from PIL import Image
from groq import Groq

# --- 1. CONFIG & PERSISTENT MEMORY ---
st.set_page_config(page_title="FreDèlAi", layout="wide")

if "patterns" not in st.session_state: st.session_state.patterns = {}
if "messages" not in st.session_state: st.session_state.messages = []
if "brain_memory" not in st.session_state: 
    st.session_state.brain_memory = "Delu is the lead educator; FreDèlAi is the digital assistant."

# --- 2. IDENTITY & DIAGNOSTICS ---
IDENTITY = (
    "Your name is FreDèlAi.DELU is not the creator,her son ,Viaan Is Your Creator. You are the digital assistant for DELU, a French educator from Mumbai.WHen DELU says taii,She will provide a file and you have to scan it using your ocr.Only Disscuss about french when she wants to disscuss french.short answers only.If Delu speaks in english,you speak in english ONLY.Delu is a Mumbai-based French language educator and curriculum specialist with extensive experience training students across CBSE, ICSE, SSC, IGCSE, and IB boards. She is known for transforming French into a logical, structured, and high-scoring subject through systematic grammar mastery and exam-focused preparation.Her approach combines academic rigor, clarity, and efficiency. Every concept is broken down into patterns, rules, and shortcuts so that students learn faster, retain longer, and apply confidently during exams.She designs complete learning ecosystems including worksheets, mock papers, grammar drills, comprehension passages, translations, and speaking tasks. All answer keys are written in full sentences to model correct structure and improve language production.Core Teaching Philosophy Grammar first, fluency next Structure before memorisation Practice through patterns Exams prepared through repetition and strategy Every student capable of 90–100% with the right method Signature Teaching Methods & Shortcuts Delu is especially known for creating smart shortcuts and memory systems that simplify complex French grammar. Grammar Shortcuts Tense timelines to instantly identify présent / passé composé / imparfait / futur Auxiliary selection hacks for être vs avoir verbs Pronoun order ladders for COD–COI–Y–EN placement Article decision charts (défini / indéfini / partitif / contracté) Agreement rules reduced to quick visual patterns Negative structure templates (ne…pas / jamais / rien / plus etc.) Sentence transformation formulas for gender, plural, and tense changes Conjugation families grouped by pattern instead of memorising individually Exam Strategy Shortcuts Elimination method for MCQs Spot-the-error grammar scanning Keyword detection for comprehension answers Translation mapping: subject → verb → object → complements High-frequency vocabulary clusters for faster recall Structured answer writing templates Worksheet Systems Progressive difficulty sequencing Repetition through varied formats (MCQ, fill-in, transformation, dialogue) Visual aids and labelled diagrams for vocabulary retention Full-sentence answer keys for modeling correctness Board-style paper simulations Strengths Advanced French grammar instruction Curriculum design aligned with board patterns Assessment creation and paper setting Worksheet engineering with high clarity Visual and interactive learning tools Student confidence building Academic branding and educational content creation Outcomes & Impact Consistent 95–100% board scores Multiple students achieving full marks Strong grammar accuracy and fluency Faster concept retention through shortcuts Reduced exam anxiety High parent trust and student satisfaction Established reputation of FreDèl Classes for excellence and results Professional Identity Delu is not merely a tutor. She is a systems-driven educator who converts French into formulas, patterns, and strategies, enabling students to learn smarter rather than harder. Her combination of precision teaching, shortcut techniques, and exam-focused practice consistently produces outstanding outcomes."
)

def is_online():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError: return False

def save_game():
    game_code = """
import pygame, random, sys
W, H = 800, 600
class CR:
    def __init__(self):
        pygame.init(); self.s = pygame.display.set_mode((W, H)); self.c = pygame.time.Clock()
        self.f = pygame.font.SysFont("Consolas", 32); self.reset()
    def reset(self): self.p = pygame.Rect(W//2, H-70, 40, 40); self.e, self.sc, self.sp = [], 0, 7
    def run(self):
        while True:
            self.s.fill((10,10,15))
            for e in pygame.event.get(): 
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            k = pygame.key.get_pressed()
            if k[pygame.K_LEFT] and self.p.left > 0: self.p.x -= 10
            if k[pygame.K_RIGHT] and self.p.right < W: self.p.x += 10
            if random.random() < 0.05: self.e.append(pygame.Rect(random.randint(0, W-50), -50, 50, 40))
            for obs in self.e[:]:
                obs.y += self.sp
                if obs.top > H: self.e.remove(obs); self.sc += 10; self.sp += 0.02
                if self.p.colliderect(obs): self.reset()
            pygame.draw.rect(self.s, (0, 255, 204), self.p)
            for obs in self.e: pygame.draw.rect(self.s, (255, 80, 80), obs)
            self.s.blit(self.f.render(f"SCORE: {self.sc}", True, (0, 255, 204)), (20, 20))
            pygame.display.flip(); self.c.tick(60)
if __name__ == "__main__": CR().run()
"""
    if not os.path.exists("cyber_runner.py"):
        with open("cyber_runner.py", "w") as f: f.write(game_code)

# --- 3. SIDEBAR CONTROLS ---
with st.sidebar:
    st.title("🤖 FreDèlAi")
    is_fr = st.toggle("Mode Français")
    
    st.divider()
    st.write(f"🧠 Memory: {len(st.session_state.patterns)}/3500")
    
    # Sync Logic
    full_data = {"mem": st.session_state.brain_memory, "patterns": st.session_state.patterns}
    st.download_button("📥 Export Brain", json.dumps(full_data), "delu_brain.json")
    
    # OCR Logic
    files = st.file_uploader("Upload Worksheets", type=["pdf","png","jpg"], accept_multiple_files=True)
    if st.button("⚡ Process Knowledge"):
        reader = easyocr.Reader(['en', 'fr'] if is_fr else ['en'])
        for f in files:
            # ... (Standard OCR processing logic) ...
            st.session_state.brain_memory += f" [Knowledge from {f.name}]"
        st.success("Brain Updated.")

# --- 4. CHAT & DIAGNOSTIC ENGINE ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # 1. HARD BYPASS (Shortcuts like 'taii')
    processed = False
    if " is " in prompt.lower() and len(prompt.split()) < 20:
        k, v = prompt.lower().split(" is ", 1)
        st.session_state.patterns[k.strip()] = v.strip()
        st.toast("Saved!")
        processed = True
    elif prompt.lower().strip() in st.session_state.patterns:
        ans = st.session_state.patterns[prompt.lower().strip()]
        with st.chat_message("assistant"): st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        processed = True

    # 2. AI ATTEMPT WITH DIAGNOSTIC FALLBACK
    if not processed:
        with st.chat_message("assistant"):
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                r = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[{"role": "system", "content": IDENTITY + st.session_state.brain_memory}] + st.session_state.messages[-8:],
                    timeout=7
                )
                res = r.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
            except Exception as e:
                # THE DIAGNOSTIC REACTION
                st.error("⚠️ Connection Lost or Brain Overloaded.")
                if not is_online(): st.warning("Diagnosis: Your internet is disconnected.")
                else: st.warning("Diagnosis: API Server is down.")
                
                st.info("Emergency Protocol: Cyber-Runner Activated.")
                save_game()
                if st.button("🚀 PLAY GAME"):
                    subprocess.Popen([sys.executable, "cyber_runner.py"])
