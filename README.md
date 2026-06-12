# Gemma 4 UEFN Game Design Planner

A premium agentic web dashboard and local orchestration planner powered by the local **Gemma 4 12B** model (via Ollama). This tool guides a **Lead Game Architect** and a **Psychological Critic** to collaborate over 4 design pillars to plan high-retention, high-engagement Fortnite UEFN games.

---

## 🚀 Pipeline & Orchestration Flow

```
[ Game Concept Input ]
         │
         ▼
 ┌───────────────┐
 │ Baseline Gen  │ ───► Phase 1: Core Pitch & UEFN Device Mapping
 └───────────────┘ ───► Phase 2: Verse Logic Architecture
         │         ───► Phase 3: Economy Balancing & Hard Math
         ▼
 ┌───────────────┐
 │  Autopilot    │ ◄─────────────────────────┐
 │  Critic Loop  │                           │
 └───────────────┘                           │ (Refinement Cycles)
         │                                   │
         ▼                                   │
   [ Critique? ] ──(Yes: Autopilot Loop) ────┤
         │                                   │
         ├───(No: Wait for User input) ──────┘
         ▼
 ┌───────────────┐
 │ Finalize GDD  │ ───► Phase 4: Dopamine & Epic Games Compliance Audit
 └───────────────┘ ───► Synthesize Final Game Design Document (GDD)
```

---

## 🌟 Key Features

* **Multi-Phase Deep Dive Pipeline**:
  - **Phase 1: Core Pitch & Device Mapping**: Maps tycoon, extraction, or PvP mechanics directly to concrete UEFN devices.
  - **Phase 2: Verse Logic Architecture**: Designs robust, persistence-enabled Verse structures and state machines.
  - **Phase 3: Economy balancing & Hard Math**: Formulates decay rates, multiplier caps, and progression curves.
  - **Phase 4: Dopamine & Retention Audit**: Performs psychological risk, spawn-camping, and Epic Games rule compliance audits.
* **Autonomous Autopilot Mode**: Loops critique-design refinement cycles continuously without requiring user input for each round.
* **Live Token-by-Token Streaming**: Streams Architect designs and Critic audits dynamically into side-by-side workspace tabs.
* **LaTeX Formula Typesetting**: Fully renders mathematical curves and volatility formulas beautifully using the **KaTeX** math typesetting engine.
* **Design Change Log & Historical Ledger**: Tracks all proposed, rejected, and implemented mechanics across iterations, preventing repetitive model suggestions.
* **Thread Session Safety & Abort Controls**: Prevents orphan background threads using Session IDs, and includes a one-click **Abort / Reset** button to interrupt hanging generations instantly.
* **GPU VRAM Optimization**: Intelligently unloads the model from graphics memory during idle wait states using Ollama `keep_alive` configurations.

---

## 🌐 Hybrid GitHub Pages + Local Architecture

This project is configured with a hybrid hosting architecture. The frontend dashboard is hosted serverless on **GitHub Pages**, while the backend orchestration engine runs locally on your machine to access high-performance GPU hardware (Ollama + Gemma 4 model) and write output documents directly.

### How it Works:
1. **Frontend Hosting**: The `docs/` folder contains the unified static UI files which are served via GitHub Pages.
2. **Dynamic Cross-Origin Requests**: The frontend detects if it's running remotely. If not on `localhost`, it automatically roots all API calls to `http://127.0.0.1:8000` (CORS-enabled backend).
3. **Local Backend Engine**: The `server.py` FastAPI runner hosts the pipeline and coordinates the LLM client, keeping generations and markdown output files local.

---

## 📋 Prerequisites

1. Install Python 3.10 or higher.
2. Install [Ollama](https://ollama.com).
3. Pull the target model in your terminal:
   ```bash
   ollama pull gemma4:latest
   ```

---

## 📦 Installation & Setup

1. Clone this repository to your local machine:
   ```bash
   git clone https://github.com/RorriMaesu/gemma4-uefn-game-planner.git
   cd gemma4-uefn-game-planner
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure the model endpoint by editing `config.json` (if your Ollama runs on a non-standard port or hostname):
   ```json
   {
     "api_type": "ollama",
     "api_url": "http://localhost:11434",
     "model_name": "gemma4:latest",
     "temperature": 0.3
   }
   ```

---

## 🏃 Running the Application

### ⚡ Option A: Auto-Launcher (Recommended)
Double-click the **`autolaunch.bat`** script in the project root directory. This script will:
- Spin up the local FastAPI background server.
- Wait for it to boot.
- Open the hosted web interface on GitHub Pages (`https://RorriMaesu.github.io/gemma4-uefn-game-planner/`) automatically.

### 🛠️ Option B: Manual Startup
1. Start the FastAPI server manually:
   ```bash
   python server.py
   ```
2. Open your web browser and navigate to:
   - Local deployment: **`http://localhost:8000`**
   - GitHub Pages interface: **`https://RorriMaesu.github.io/gemma4-uefn-game-planner/`**

---

## 🧪 Running Tests

Validate the server integration and client loop using Python's built-in unittest tool:
```bash
# Run FastAPI endpoint and thread lifecycle tests
python -m unittest test_server.py

# Run client pipeline mock tests
python -m unittest test_planner.py
```
