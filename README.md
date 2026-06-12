# Gemma 4 UEFN Game Design Planner

A premium agentic web dashboard and local orchestration planner powered by the local **Gemma 4 12B** model (via Ollama). This tool guides a **Lead Game Architect** and a **Psychological Critic** to collaborate over 4 design pillars to plan high-retention, high-engagement Fortnite **UEFN (Unreal Editor for Fortnite)** games.

🎮 **Access the live dashboard on GitHub Pages**: [gemma4-uefn-game-planner Web UI](https://RorriMaesu.github.io/gemma4-uefn-game-planner/)

---

## 🚀 Pipeline & Orchestration Flow

```
[ Game Concept Input ]
         │
         ▼
 ┌───────────────┐
 │ Baseline Gen  │ ───► Phase 1: Core Pitch & UEFN Device Mapping
 └───────────────┘ ───► Phase 2: Verse Programming Logic Architecture
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
  - **Phase 1: Core Pitch & Device Mapping**: Maps tycoon, extraction, or Player-vs-Player (PvP) mechanics directly to concrete Unreal Editor for Fortnite (UEFN) devices.
  - **Phase 2: Verse Logic Architecture**: Designs robust, persistence-enabled Verse programming language structures and state machines.
  - **Phase 3: Economy balancing & Hard Math**: Formulates progression curves, multipliers, and math formulas.
  - **Phase 4: Dopamine & Retention Audit**: Performs audits for psychological player risk, spawn-camping issues, and Epic Games creator rule compliance.
* **Autonomous Autopilot Mode**: Loops critique-design refinement cycles continuously without requiring manual user approval for each round.
* **Live Token-by-Token Streaming**: Streams Architect designs and Critic audits dynamically into side-by-side workspace tabs.
* **LaTeX Formula Typesetting**: Renders mathematical curves and volatility formulas beautifully in the browser using the **KaTeX** math typesetting engine.
* **Design Change Log & Historical Ledger**: Tracks all proposed, rejected, and implemented mechanics across iterations to prevent the AI from repeating the same suggestions.
* **Thread Session Safety & Abort Controls**: Prevents orphan background processing threads using session identifiers, and includes a one-click **Abort / Reset** button to stop hanging generations instantly.
* **VRAM (Video Memory) Optimization**: Intelligently unloads the model from the graphics card's Video Random Access Memory (VRAM) during idle wait states to free up computer resources.

---

## 🌐 Hybrid GitHub Pages + Local Architecture

This project is configured with a hybrid hosting architecture. The frontend web interface (the dashboard) is hosted serverless on **GitHub Pages**, while the backend orchestration engine runs locally on your machine to access your graphics card (GPU) and write output documents directly.

### How it Works:
1. **Frontend Hosting**: The `docs/` folder contains the unified static User Interface (UI) files which are served via GitHub Pages.
2. **Dynamic Cross-Origin Requests**: The frontend detects if it's running remotely. If it is hosted on GitHub Pages, it automatically routes all backend calls to your local machine at `http://127.0.0.1:8000` using **CORS (Cross-Origin Resource Sharing)**.
3. **Local Backend Engine**: The `server.py` server runner hosts the pipeline and coordinates the local Large Language Model (LLM) client, keeping your generations and markdown output files local.

---

## 📋 Prerequisites

1. Install Python 3.10 or higher.
2. Install [Ollama](https://ollama.com).
3. Download the target model in your command terminal:
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
- Wait for it to start.
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

---

## 📖 Glossary of Terms & Abbreviations

To help you understand the terms used in this project, here is a quick reference guide:

| Abbreviation / Term | Full Name | Description |
| :--- | :--- | :--- |
| **UEFN** | Unreal Editor for Fortnite | A tool used to design and publish custom games inside Fortnite. |
| **Verse** | Verse Programming Language | Epic Games' programming language used to write custom gameplay logic in UEFN. |
| **GDD** | Game Design Document | A blueprint document detailing the mechanics, design, and loop of a video game. |
| **LLM** | Large Language Model | A type of artificial intelligence (like Gemma 4) trained to understand and generate text. |
| **VRAM** | Video Random Access Memory | Specialized high-speed computer memory used by graphics cards to run heavy models. |
| **GPU** | Graphics Processing Unit | The graphics card hardware in your computer that handles parallel math processing. |
| **CORS** | Cross-Origin Resource Sharing | A security mechanism that allows web pages to request resources from a different domain/port (like GitHub Pages talking to localhost). |
| **FastAPI** | FastAPI | A modern, fast web framework for building Application Programming Interfaces (APIs) in Python. |
| **KaTeX** | KaTeX | A fast JavaScript library that displays mathematical formulas beautifully on web pages. |
| **LaTeX** | LaTeX | A typesetting system used for writing scientific documents and mathematical formulas. |
| **UI** | User Interface | The visual elements (buttons, text fields, tabs) that a person interacts with on a website. |
| **API** | Application Programming Interface | A software intermediary that allows two applications (like the web front-end and Python back-end) to talk to each other. |
