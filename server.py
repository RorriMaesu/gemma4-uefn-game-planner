import os
import sys
import json
import threading
import traceback
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add current workspace to path to import client
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from planner import LocalLLMClient, load_prompt_file

app = FastAPI(title="Game Design Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared thread-safe state object
class PlannerState:
    def __init__(self):
        self.phase = "idle"  # idle, phase1, phase2, phase3, refinement, phase4, finished
        self.is_waiting = False
        self.vram_status = "Unloaded"
        self.architect_content = ""
        self.critic_content = ""
        self.final_gdd = ""
        self.logs = []
        self.concept = ""
        self.autopilot = True
        self.session_id = 0
        
        # Thread sync
        self.user_action_event = threading.Event()
        self.next_action = None  # C, F, Q
        self.next_focus = ""
        self.thread: Optional[threading.Thread] = None
        self.client: Optional[LocalLLMClient] = None
        self.lock = threading.Lock()

    def log(self, message: str):
        with self.lock:
            self.logs.append(message)
            print(message)  # Print to terminal output too

    def reset(self, concept: str):
        with self.lock:
            self.phase = "idle"
            self.is_waiting = False
            self.vram_status = "Unloaded"
            self.architect_content = ""
            self.critic_content = ""
            self.final_gdd = ""
            self.logs = []
            self.concept = concept
            self.autopilot = True
            self.session_id += 1
            self.next_action = None
            self.next_focus = ""
            self.user_action_event.clear()

global_state = PlannerState()

# Request schemas
class StartRequest(BaseModel):
    concept: str

class ActionRequest(BaseModel):
    action: str  # C, F, Q
    focus: Optional[str] = ""

# The Background Orchestrator Thread Loop
def run_orchestration_loop(state: PlannerState, output_dir: str):
    local_session_id = state.session_id
    try:
        def check_abort():
            if state.session_id != local_session_id:
                raise InterruptedError()

        state.log(f"[System] Starting generation for concept: '{state.concept}'")
        
        # Load Client (checks config.json automatically)
        is_mock = os.getenv("PLANNER_MOCK") == "1"
        state.client = LocalLLMClient(config_path="config.json", mock=is_mock)
        if state.client.mock:
            state.log("[System] Local LLM unavailable. Running in Mock Mode.")
        else:
            state.log(f"[System] Connected to {state.client.api_type} at {state.client.api_url} using model {state.client.model}.")

        check_abort()
        state.vram_status = "Active"
        
        # Load Prompt Templates
        architect_system = load_prompt_file("prompts/architect_system.txt")
        critic_system = load_prompt_file("prompts/critic_system.txt")

        # ==========================================
        # PHASE 1: Pitch & Devices
        # ==========================================
        check_abort()
        state.phase = "phase1"
        state.log("[System] Running Phase 1: Core Pitch & UEFN Device Mapping...")
        phase1_tmpl = load_prompt_file("prompts/phase1_instructions.txt")
        arch_inst = phase1_tmpl.split("[CRITIC INSTRUCTIONS]")[0].replace("[ARCHITECT INSTRUCTIONS]", "").strip()
        crit_inst = phase1_tmpl.split("[CRITIC INSTRUCTIONS]")[1].strip()

        # Run Architect
        state.architect_content = ""
        for chunk in state.client.generate_stream(architect_system, arch_inst.format(game_concept=state.concept)):
            check_abort()
            state.architect_content += chunk
        arch_p1 = state.architect_content
        with open(os.path.join(output_dir, "phase1_architect_pitch.md"), "w", encoding="utf-8") as f:
            f.write(arch_p1)

        # Run Critic
        state.critic_content = ""
        for chunk in state.client.generate_stream(critic_system, crit_inst + f"\n\nArchitect Output:\n{arch_p1}"):
            check_abort()
            state.critic_content += chunk
        crit_p1 = state.critic_content
        with open(os.path.join(output_dir, "phase1_critic_audit.md"), "w", encoding="utf-8") as f:
            f.write(crit_p1)
        state.log("[System] Phase 1 Baseline Complete.")

        # ==========================================
        # PHASE 2: Verse & State
        # ==========================================
        check_abort()
        state.phase = "phase2"
        state.log("[System] Running Phase 2: Verse Logic Architecture...")
        phase2_tmpl = load_prompt_file("prompts/phase2_instructions.txt")
        arch_inst = phase2_tmpl.split("[CRITIC INSTRUCTIONS]")[0].replace("[ARCHITECT INSTRUCTIONS]", "").strip()
        crit_inst = phase2_tmpl.split("[CRITIC INSTRUCTIONS]")[1].strip()

        # Run Architect
        state.architect_content = ""
        for chunk in state.client.generate_stream(architect_system, arch_inst.format(
            phase1_architect=arch_p1,
            phase1_critic=crit_p1
        )):
            check_abort()
            state.architect_content += chunk
        arch_p2 = state.architect_content
        with open(os.path.join(output_dir, "phase2_architect_verse.md"), "w", encoding="utf-8") as f:
            f.write(arch_p2)

        # Run Critic
        state.critic_content = ""
        for chunk in state.client.generate_stream(critic_system, crit_inst + f"\n\nArchitect Output:\n{arch_p2}"):
            check_abort()
            state.critic_content += chunk
        crit_p2 = state.critic_content
        with open(os.path.join(output_dir, "phase2_critic_audit.md"), "w", encoding="utf-8") as f:
            f.write(crit_p2)
        state.log("[System] Phase 2 Baseline Complete.")

        # ==========================================
        # PHASE 3: Economy & Math
        # ==========================================
        check_abort()
        state.phase = "phase3"
        state.log("[System] Running Phase 3: Economy Balancing & Hard Math...")
        phase3_tmpl = load_prompt_file("prompts/phase3_instructions.txt")
        arch_inst = phase3_tmpl.split("[CRITIC INSTRUCTIONS]")[0].replace("[ARCHITECT INSTRUCTIONS]", "").strip()
        crit_inst = phase3_tmpl.split("[CRITIC INSTRUCTIONS]")[1].strip()

        # Run Architect
        state.architect_content = ""
        for chunk in state.client.generate_stream(architect_system, arch_inst.format(
            phase2_architect=arch_p2,
            phase2_critic=crit_p2
        )):
            check_abort()
            state.architect_content += chunk
        arch_p3 = state.architect_content
        with open(os.path.join(output_dir, "phase3_architect_economy.md"), "w", encoding="utf-8") as f:
            f.write(arch_p3)

        # Run Critic
        state.critic_content = ""
        for chunk in state.client.generate_stream(critic_system, crit_inst + f"\n\nArchitect Output:\n{arch_p3}"):
            check_abort()
            state.critic_content += chunk
        crit_p3 = state.critic_content
        with open(os.path.join(output_dir, "phase3_critic_audit.md"), "w", encoding="utf-8") as f:
            f.write(crit_p3)
        state.log("[System] Phase 3 Baseline Complete.")

        # Compile Baseline Draft
        check_abort()
        current_draft = (
            f"# Core Game Design Draft\n\n"
            f"## Baseline Concept & Devices\n{arch_p1}\n\n"
            f"## State & Verse Logic\n{arch_p2}\n\n"
            f"## Economy & Math Balance\n{arch_p3}"
        )
        with open(os.path.join(output_dir, "baseline_draft.md"), "w", encoding="utf-8") as f:
            f.write(current_draft)
        state.log("[System] Baseline Game Design Draft compiled and saved.")

        # ==========================================
        # INTERACTIVE REFINEMENT LOOP
        # ==========================================
        state.phase = "refinement"
        iteration = 1

        while True:
            check_abort()
            # Check if we should wait for user action
            if not state.autopilot:
                state.log("[System] Entering Wait State (Manual Mode). Unloading model from VRAM to free GPU memory...")
                state.client.unload_model()
                state.vram_status = "Unloaded"
                state.is_waiting = True

                # Wait for user button trigger
                state.user_action_event.wait()
                state.user_action_event.clear()
                state.is_waiting = False
                state.vram_status = "Active"
            else:
                state.vram_status = "Active"
                state.is_waiting = False

            check_abort()
            if state.next_action == 'q' or state.next_action == 'f':
                break

            # Process refinement cycle
            focus = state.next_focus
            
            # Reset actions for the next loop
            state.next_action = None
            state.next_focus = ""
            
            state.log(f"[System] Starting Refinement Cycle {iteration} (Focus: '{focus if focus else 'General Critique'}')...")
            
            # Critique
            critic_prompt = (
                f"Critique the current design draft considering this custom focus: '{focus if focus else 'General Audit'}'\n\n"
                f"Current Game Design Draft:\n{current_draft}"
            )
            state.critic_content = ""
            for chunk in state.client.generate_stream(critic_system, critic_prompt, keep_alive="5m"):
                check_abort()
                state.critic_content += chunk
            critic_feedback = state.critic_content
            with open(os.path.join(output_dir, f"refinement_cycle_{iteration}_critic.md"), "w", encoding="utf-8") as f:
                f.write(critic_feedback)

            # Architect Update
            arch_prompt = (
                f"Incorporate the Critic's audit and user guidelines into the design draft:\n"
                f"User Guidelines: '{focus}'\n"
                f"Critic Audit:\n{critic_feedback}\n\n"
                f"Current Game Design Draft:\n{current_draft}"
            )
            state.architect_content = ""
            for chunk in state.client.generate_stream(architect_system, arch_prompt, keep_alive="5m"):
                check_abort()
                state.architect_content += chunk
            updated_draft = state.architect_content
            current_draft = updated_draft
            with open(os.path.join(output_dir, f"refinement_cycle_{iteration}_architect.md"), "w", encoding="utf-8") as f:
                f.write(updated_draft)

            state.log(f"[System] Refinement Cycle {iteration} Complete.")
            iteration += 1

            # Autopilot review sleep
            if state.autopilot:
                import time
                state.log("[System] Autopilot: Pausing 3 seconds for review before next cycle...")
                for _ in range(15):
                    if not state.autopilot or state.next_action in ('f', 'q', 'c') or state.session_id != local_session_id:
                        break
                    time.sleep(0.2)

        # ==========================================
        # PHASE 4: Dopamine Audit & Final Synthesis
        # ==========================================
        check_abort()
        if state.next_action == 'f':
            state.phase = "phase4"
            state.log("[System] Finalizing. Compiling retention metrics and synthesizing GDD...")
            phase4_tmpl = load_prompt_file("prompts/phase4_instructions.txt")
            crit_inst = phase4_tmpl.split("[ARCHITECT INSTRUCTIONS]")[0].replace("[CRITIC INSTRUCTIONS]", "").strip()
            arch_inst = phase4_tmpl.split("[ARCHITECT INSTRUCTIONS]")[1].strip()

            # Critic Dopamine Audit
            crit_prompt = crit_inst.format(
                phase3_architect=current_draft,
                phase3_critic="Review the current refined draft mechanics"
            )
            state.critic_content = ""
            for chunk in state.client.generate_stream(critic_system, crit_prompt, keep_alive="5m"):
                check_abort()
                state.critic_content += chunk
            dopamine_audit = state.critic_content
            with open(os.path.join(output_dir, "final_dopamine_audit.md"), "w", encoding="utf-8") as f:
                f.write(dopamine_audit)

            # Architect Synthesizes GDD
            arch_prompt = arch_inst.format(
                phase3_architect=current_draft,
                phase3_critic="Synthesize the whole refined game loop"
            )
            arch_prompt += f"\n\nCritic's Dopamine & Retention Audit:\n{dopamine_audit}"
            
            state.final_gdd = ""
            for chunk in state.client.generate_stream(architect_system, arch_prompt, keep_alive="0"):
                check_abort()
                state.final_gdd += chunk
            final_gdd = state.final_gdd
            
            final_gdd_path = os.path.join(output_dir, "game_design_document.md")
            with open(final_gdd_path, "w", encoding="utf-8") as f:
                f.write(final_gdd)

            state.log("[System] Final synthesis compiled successfully!")

        check_abort()
        state.phase = "finished"
        state.client.unload_model()
        state.vram_status = "Unloaded"
        state.log("[System] Design process completed successfully.")

    except InterruptedError:
        print(f"[System] Thread for session {local_session_id} aborted cleanly.")
    except Exception as e:
        if state.session_id == local_session_id:
            state.phase = "finished"
            state.is_waiting = False
            state.vram_status = "Unloaded"
            state.log(f"[Error] Execution thread failed: {e}")
            state.log(traceback.format_exc())

# API Endpoints
@app.post("/api/start")
def start_planner(req: StartRequest):
    if global_state.phase not in ("idle", "finished"):
        raise HTTPException(status_code=400, detail="Orchestration already running")

    global_state.reset(req.concept)
    
    # Run loop in background thread
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    global_state.thread = threading.Thread(
        target=run_orchestration_loop, 
        args=(global_state, output_dir),
        daemon=True
    )
    global_state.thread.start()
    return {"status": "started"}

@app.post("/api/abort")
def abort_planner():
    # Increment session ID to cancel any running threads
    global_state.session_id += 1
    if global_state.client:
        global_state.client.unload_model()
    global_state.phase = "finished"
    global_state.is_waiting = False
    global_state.vram_status = "Unloaded"
    global_state.log("[System] Generation aborted manually by user.")
    return {"status": "ok"}

class AutopilotRequest(BaseModel):
    enable: bool

@app.get("/api/status")
def get_status():
    return {
        "phase": global_state.phase,
        "is_waiting": global_state.is_waiting,
        "vram_status": global_state.vram_status,
        "architect_content": global_state.architect_content,
        "critic_content": global_state.critic_content,
        "final_gdd": global_state.final_gdd,
        "logs": global_state.logs,
        "autopilot": global_state.autopilot
    }

@app.post("/api/autopilot/toggle")
def toggle_autopilot(req: AutopilotRequest):
    global_state.autopilot = req.enable
    global_state.log(f"[System] Autopilot Mode set to: {req.enable}")
    if req.enable and global_state.is_waiting:
        global_state.user_action_event.set()
    return {"status": "ok", "autopilot": global_state.autopilot}

@app.post("/api/action")
def trigger_action(req: ActionRequest):
    action_lower = req.action.lower()
    # If in autopilot, we allow intercepting finalize, quit, or refinement actions immediately
    if global_state.autopilot:
        if action_lower in ('f', 'q', 'c'):
            global_state.next_action = action_lower
            if action_lower == 'c':
                global_state.next_focus = req.focus
            return {"status": "ok"}
        raise HTTPException(status_code=400, detail="Invalid action for autopilot mode")
        
    if not global_state.is_waiting:
        raise HTTPException(status_code=400, detail="State not waiting for user action")
    
    global_state.next_action = action_lower
    global_state.next_focus = req.focus
    global_state.user_action_event.set()
    return {"status": "ok"}

@app.post("/api/vram/unload")
def force_unload():
    if global_state.client:
        global_state.client.unload_model()
        global_state.vram_status = "Unloaded"
        global_state.log("[System] Model unloaded manually from dashboard.")
        return {"status": "ok"}
    raise HTTPException(status_code=400, detail="LLM Client not initialized")

# Serve UI static files
app.mount("/", StaticFiles(directory="docs", html=True), name="static")

def try_start_ollama():
    import urllib.request
    import os
    import subprocess
    try:
        # Check if Ollama service is already responding
        urllib.request.urlopen("http://127.0.0.1:11434", timeout=1)
        print("[System] Ollama service is already running.")
    except Exception:
        print("[System] Ollama service not responding. Attempting to auto-launch Ollama application...")
        # Array of common Windows 11 installation locations for Ollama app or daemon
        candidate_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama app.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\Ollama\ollama app.exe"),
            os.path.expandvars(r"%SystemDrive%\Users\%USERNAME%\AppData\Local\Programs\Ollama\ollama app.exe"),
            r"C:\Users\Tesla\AppData\Local\Programs\Ollama\ollama app.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\Ollama\ollama.exe"),
            r"C:\Program Files\Ollama\ollama.exe"
        ]
        
        launched = False
        for path in candidate_paths:
            if os.path.exists(path):
                try:
                    subprocess.Popen([path])
                    print(f"[System] Ollama application launched successfully from: {path}")
                    launched = True
                    break
                except Exception as e:
                    print(f"[Warning] Failed to launch Ollama from {path}: {e}")
        
        if not launched:
            print("[Warning] Ollama installation not found at common locations. Please ensure Ollama is running manually.")

if __name__ == "__main__":
    import uvicorn
    # Auto-start Ollama if it is shut down
    try_start_ollama()
    # Launch uvicorn server at localhost:8000
    uvicorn.run(app, host="127.0.0.1", port=8000)
