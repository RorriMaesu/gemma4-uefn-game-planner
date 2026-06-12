# Gemma 4 UEFN Game Design Planner

A premium agentic web dashboard and local orchestration planner powered by the local **Gemma 4 12B** model (via Ollama). This tool guides a **Lead Game Architect** and a **Psychological Critic** to collaborate over 4 design pillars to plan high-retention, high-engagement Fortnite UEFN games.

---

## 🚀 Key Features

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

## 🛠️ Architecture

* **Backend**: FastAPI web server running in Python, managing the background orchestration loop inside a thread-safe daemon state.
* **Frontend**: Responsive, modern dark-mode glassmorphic single-page web app built with vanilla HTML5, CSS3, and JavaScript. Uses `marked.js` and `katex` for rich rendering.
* **LLM Integration**: Connects via HTTP streams to a local Ollama server running the `gemma4:latest` model.

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

1. Clone this repository (or copy the files into a workspace directory).
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

1. Start the FastAPI server:
   ```bash
   python server.py
   ```
2. Open your web browser and navigate to: **`http://localhost:8000`**
3. Type in your game idea (e.g., *"A cyberpunk heist game with volatile stock markets and extraction vaults"*), click **Generate Baseline Plan**, and watch the loop refine the design autonomously!

---

## 🧪 Running Tests

Validate the server integration and client loop using Python's built-in unittest tool:
```bash
# Run FastAPI endpoint and thread lifecycle tests
python -m unittest test_server.py

# Run client pipeline mock tests
python -m unittest test_planner.py
```
