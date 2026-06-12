#!/usr/bin/env python3
import os
import sys
import json
import argparse
import requests
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.status import Status
from rich.progress import Progress, SpinnerColumn, TextColumn

# Reconfigure stdout/stderr to UTF-8 to handle Unicode/emojis on Windows consoles
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

console = Console()

class LocalLLMClient:
    def __init__(self, config_path="config.json", mock=False):
        self.mock = mock
        self.config = {
            "api_type": "ollama",
            "api_url": "http://localhost:11434",
            "model_name": "gemma4:12b",
            "temperature": 0.3,
            "max_tokens": 4096
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read config.json, using defaults. Error: {e}[/]")

        self.api_type = self.config["api_type"].lower()
        self.api_url = self.config["api_url"]
        self.model = self.config["model_name"]
        self.temperature = self.config["temperature"]

    def generate_stream(self, system_prompt: str, prompt_content: str, keep_alive: str = "5m"):
        if self.mock:
            import time
            full_response = self._mock_response(system_prompt, prompt_content)
            words = full_response.split(" ")
            # Yield in small groups to simulate typing
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i:i+3]) + " "
                yield chunk
                time.sleep(0.015)
            return

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_content}
        ]

        try:
            if self.api_type == "ollama":
                url = f"{self.api_url.rstrip('/')}/api/chat"
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                    "keep_alive": keep_alive,
                    "options": {
                        "temperature": self.temperature
                    }
                }
                response = requests.post(url, json=payload, stream=True, timeout=120)
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line.decode("utf-8"))
                        content_chunk = chunk.get("message", {}).get("content", "")
                        yield content_chunk
            
            elif self.api_type in ("openai", "openai-compatible"):
                url = f"{self.api_url.rstrip('/')}/chat/completions"
                headers = {"Content-Type": "application/json"}
                if "api_key" in self.config:
                    headers["Authorization"] = f"Bearer {self.config['api_key']}"
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "stream": True
                }
                response = requests.post(url, json=payload, headers=headers, stream=True, timeout=120)
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode("utf-8").strip()
                        if line_str.startswith("data: "):
                            data_content = line_str[6:]
                            if data_content == "[DONE]":
                                break
                            chunk = json.loads(data_content)
                            content_chunk = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            yield content_chunk
            else:
                raise ValueError(f"Unsupported API type: {self.api_type}")

        except Exception as e:
            console.print(f"[red]Error connecting to LLM endpoint ({self.api_url}): {e}[/]")
            console.print("[yellow]Switching automatically to Mock Mode to continue dry-run...[/]")
            self.mock = True
            yield from self.generate_stream(system_prompt, prompt_content, keep_alive)

    def generate(self, system_prompt: str, prompt_content: str, keep_alive: str = "5m") -> str:
        full_content = ""
        for chunk in self.generate_stream(system_prompt, prompt_content, keep_alive):
            full_content += chunk
        return full_content

    def unload_model(self) -> None:
        """Intelligently unloads the model from VRAM by requesting keep_alive: 0 with empty messages."""
        if self.mock or self.api_type != "ollama":
            return
        try:
            url = f"{self.api_url.rstrip('/')}/api/chat"
            payload = {
                "model": self.model,
                "messages": [],
                "keep_alive": 0
            }
            # Fast request to trigger unload
            requests.post(url, json=payload, timeout=5)
            console.print("[dim cyan]VRAM Cleaned: Model unloaded from GPU.[/]")
        except Exception:
            pass

    def _mock_response(self, system_prompt: str, prompt_content: str) -> str:
        is_architect = "Lead Game Architect" in system_prompt
        
        if "PHASE 1" in prompt_content or "Phase 1" in prompt_content:
            if is_architect:
                return """# Game Design: Cyberpunk Vault Raiders

### 1. 🎮 CONCRETE UEFN DEVICE MAPPING
*   `mutator_zone_device`:
    *   Set 'Zone Width' to `20.0`
    *   Set 'Zone Depth' to `20.0`
    *   Set 'Zone Height' to `6.0`
    *   Set 'Weapon Fire Affects Zone' to `False`
    *   Set 'Enabled on Minigame Start' to `True`
*   `conditional_button_device`:
    *   Set 'Key Items Required' to `1`
    *   Set 'Consume Key Items' to `True`
    *   Set 'Trigger Delay' to `0.5`
"""
            else:
                return """### 1. 🎮 UEFN DEVICE CONFLICT & LIMITATION AUDIT
*   **Conflict Detected**: The `mutator_zone_device` zone height of `6.0` might clipping-conflict with low ceilings if players construct platforms. Suggest setting 'Zone Height' to `5.0`.
*   **Limitation**: A single `conditional_button_device` cannot check for multiple item types sequentially. Recommend cascading two buttons.
"""

        elif "PHASE 2" in prompt_content or "Phase 2" in prompt_content:
            if is_architect:
                return """### 2. 💻 VERSE LOGIC ARCHITECTURE
```verse
# Persistent data structs
player_perk_data := struct<persistable>:
    Level : int = 1
    CurrentXP : int = 0
    SelectedPerks : []string = array{}

# Thread-safe desync-proof logic
cyber_manager_device := class(creative_device):
    var PlayerDataMap : weak_map(player, player_perk_data) = map{}

    OnBegin<override>() : void =
        Print("Cyberpunk Vault Raiders Initialized")
```
"""
            else:
                return """### 2. 💻 VERSE TRANSACTION & STATE INTEGRITY AUDIT
*   **Desync Risk**: The `PlayerDataMap` uses a `weak_map` which is excellent, but modifying it inside async callbacks can lead to write conflicts. Recommend introducing transactional state validation blocks.
*   **Memory Footprint**: Ensure arrays inside the struct do not exceed Epic's persistence limits of 128KB per player.
"""

        elif "PHASE 3" in prompt_content or "Phase 3" in prompt_content:
            if is_architect:
                return """### 3. 📊 ECONOMY BALANCING & HARD MATH
*   **Base Ticking Rate**: 5 credits every 10 seconds.
*   **Center Vault Multiplier**:
    $$Multiplier = 1.0 + (t \times 0.1)$$
    up to a hard cap of 5.0x after 40 seconds of control.
*   **Shield Depleted Penalty**: Losing shield applies a $0.60$ multiplier (40% drop) to credit income.
"""
            else:
                return """### 3. 📊 ECONOMY BALANCING & MATH STRESS-TEST
*   **Snowball Risk**: A multiplier of 5.0x is too high. A player holding the vault for 40 seconds earns 25 credits per tick, creating a 5x wealth disparity. Recommend reducing the hard cap multiplier to 3.0x.
"""

        elif "refinement" in prompt_content.lower() or "critique the current" in prompt_content.lower():
            if is_architect:
                return """### Current Refinement Draft (Iterated)
*   **Updated Mechanics**: Added high-tier vault tax (10% credit fee) for players over level 10 to balance late-game advantage.
*   **Device Configuration**: Updated `mutator_zone_device` to support dynamic gravity scales.
"""
            else:
                return """### Critic Iteration Audit
*   **Balance Vulnerability**: The vault tax is good, but level 10 players can still bypass it by gifting currency. Recommend restricting peer-to-peer trading.
"""

        elif any(kw in prompt_content for kw in ["PHASE 4", "Phase 4", "Dopamine", "dopamine", "GDD", "gdd"]):
            if is_architect:
                return """# Final Game Design Document: Cyberpunk Vault Raiders

## 1. 🎮 CONCRETE UEFN DEVICE MAPPING
*   `mutator_zone_device`:
    *   Set 'Zone Width' to `20.0`
    *   Set 'Zone Depth' to `20.0`
    *   Set 'Zone Height' to `5.0`
    *   Set 'Weapon Fire Affects Zone' to `False`
*   `conditional_button_device`:
    *   Set 'Key Items Required' to `1`
    *   Set 'Consume Key Items' to `True`

## 2. 💻 VERSE LOGIC ARCHITECTURE
```verse
player_perk_data := struct<persistable>:
    Level : int = 1
    CurrentXP : int = 0
    SelectedPerks : []string = array{}
```

## 3. 📊 ECONOMY BALANCING & HARD MATH
*   Base ticking rate: 5 credits per 10s.
*   Vault Multiplier: $1.0 + (t \times 0.05)$ up to a hard cap of 3.0x.
*   Income Penalty: 40% penalty (0.6x) on shield loss.

## 4. 🧠 THE DOPAMINE & RETENTION AUDIT
*   **Variable Reward Schedule**: Vault opening triggers a Variable Ratio schedule with a 1-in-10 chance of spawning a legendary weapon core.
*   **Beginner Protection Shield**: Safe Spawn Zones prevent spawn-camping by applying a UEFN `mutator_zone_device` that disables weapon damage for the first 10 seconds post-spawn.
"""
            else:
                return """### 4. 🧠 THE DOPAMINE & RETENTION AUDIT
*   **Variable Reward Schedule**: The variable ratio schedule (1-in-10 drop) leverages unpredictable dopamine spikes.
*   **Beginner Protection**: A 10-second weapon-disable zone at spawns prevents camp exploitation effectively.
"""
        return "Mock Response"

def load_prompt_file(path):
    if not os.path.exists(path):
        console.print(f"[red]Error: Prompt file not found at {path}[/]")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def main():
    parser = argparse.ArgumentParser(description="Iterative Agentic Game Design Planner")
    parser.add_argument("--concept", type=str, help="Initial game idea/concept to develop")
    parser.add_argument("--mock", action="store_true", help="Force Run in Mock Mode")
    parser.add_argument("--output-dir", type=str, default="output", help="Directory to save outputs")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    console.print(Panel.fit(
        "[bold cyan]Gemma 4 12B - Agentic Game Design Planner[/]\n"
        "[green]Multi-Phase Interactive Refinement Loop & VRAM Optimizer[/]",
        border_style="cyan"
    ))

    client = LocalLLMClient(mock=args.mock)
    if client.mock:
        console.print("[yellow]Running in MOCK MODE (No API calls will be made)[/]")
    else:
        console.print(f"[green]Connected to API: {client.api_type} at {client.api_url} using model {client.model}[/]")

    game_concept = args.concept
    if not game_concept:
        game_concept = console.input("[bold yellow]Enter your core game concept: [/]")
        if not game_concept.strip():
            console.print("[red]Concept cannot be empty. Exiting.[/]")
            sys.exit(1)

    architect_system = load_prompt_file("prompts/architect_system.txt")
    critic_system = load_prompt_file("prompts/critic_system.txt")

    outputs = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        # PHASE 1
        p1_task = progress.add_task("[cyan]Executing Phase 1: Core Pitch & UEFN Device Mapping...", total=None)
        phase1_tmpl = load_prompt_file("prompts/phase1_instructions.txt")
        arch_inst_part = phase1_tmpl.split("[CRITIC INSTRUCTIONS]")[0].replace("[ARCHITECT INSTRUCTIONS]", "").strip()
        crit_inst_part = phase1_tmpl.split("[CRITIC INSTRUCTIONS]")[1].strip()

        outputs["phase1_architect"] = client.generate(architect_system, arch_inst_part.format(game_concept=game_concept))
        outputs["phase1_critic"] = client.generate(critic_system, crit_inst_part + f"\n\nArchitect Output:\n{outputs['phase1_architect']}")
        
        with open(os.path.join(args.output_dir, "phase1_architect_pitch.md"), "w", encoding="utf-8") as f:
            f.write(outputs["phase1_architect"])
        with open(os.path.join(args.output_dir, "phase1_critic_audit.md"), "w", encoding="utf-8") as f:
            f.write(outputs["phase1_critic"])
        progress.update(p1_task, completed=True, description="[green]Phase 1 Baseline Complete![/]")

        # PHASE 2
        p2_task = progress.add_task("[cyan]Executing Phase 2: Verse Logic Architecture...", total=None)
        phase2_tmpl = load_prompt_file("prompts/phase2_instructions.txt")
        arch_inst_part = phase2_tmpl.split("[CRITIC INSTRUCTIONS]")[0].replace("[ARCHITECT INSTRUCTIONS]", "").strip()
        crit_inst_part = phase2_tmpl.split("[CRITIC INSTRUCTIONS]")[1].strip()

        outputs["phase2_architect"] = client.generate(architect_system, arch_inst_part.format(
            phase1_architect=outputs["phase1_architect"],
            phase1_critic=outputs["phase1_critic"]
        ))
        outputs["phase2_critic"] = client.generate(critic_system, crit_inst_part + f"\n\nArchitect Output:\n{outputs['phase2_architect']}")
        
        with open(os.path.join(args.output_dir, "phase2_architect_verse.md"), "w", encoding="utf-8") as f:
            f.write(outputs["phase2_architect"])
        with open(os.path.join(args.output_dir, "phase2_critic_audit.md"), "w", encoding="utf-8") as f:
            f.write(outputs["phase2_critic"])
        progress.update(p2_task, completed=True, description="[green]Phase 2 Baseline Complete![/]")

        # PHASE 3
        p3_task = progress.add_task("[cyan]Executing Phase 3: Economy Balancing & Hard Math...", total=None)
        phase3_tmpl = load_prompt_file("prompts/phase3_instructions.txt")
        arch_inst_part = phase3_tmpl.split("[CRITIC INSTRUCTIONS]")[0].replace("[ARCHITECT INSTRUCTIONS]", "").strip()
        crit_inst_part = phase3_tmpl.split("[CRITIC INSTRUCTIONS]")[1].strip()

        outputs["phase3_architect"] = client.generate(architect_system, arch_inst_part.format(
            phase2_architect=outputs["phase2_architect"],
            phase2_critic=outputs["phase2_critic"]
        ))
        outputs["phase3_critic"] = client.generate(critic_system, crit_inst_part + f"\n\nArchitect Output:\n{outputs['phase3_architect']}")
        
        with open(os.path.join(args.output_dir, "phase3_architect_economy.md"), "w", encoding="utf-8") as f:
            f.write(outputs["phase3_architect"])
        with open(os.path.join(args.output_dir, "phase3_critic_audit.md"), "w", encoding="utf-8") as f:
            f.write(outputs["phase3_critic"])
        progress.update(p3_task, completed=True, description="[green]Phase 3 Baseline Complete![/]")

    # Compile baseline design draft
    current_draft = (
        f"# Core Game Design Draft\n\n"
        f"## Baseline Concept & Devices\n{outputs['phase1_architect']}\n\n"
        f"## State & Verse Logic\n{outputs['phase2_architect']}\n\n"
        f"## Economy & Math Balance\n{outputs['phase3_architect']}"
    )
    
    # Save base design
    with open(os.path.join(args.output_dir, "baseline_draft.md"), "w", encoding="utf-8") as f:
        f.write(current_draft)

    console.print("\n[bold green]Baseline Game Design Compiled successfully![/]")
    
    iteration = 1
    # Interactive loop
    while True:
        # VRAM Management: Clean VRAM when waiting for user input
        console.print("[dim cyan]Entering Wait State. Unloading model from GPU VRAM...[/]")
        client.unload_model()

        console.print("\n[bold yellow]=== Refinement Loop Panel ===[/]")
        console.print("[green][C][/green] Continue refinement cycle (criticism & update loop)")
        console.print("[green][F][/green] Finalize and compile Game Design Document (GDD)")
        console.print("[green][Q][/green] Quit (Exit without finalizing GDD)")
        
        action = console.input("\nChoose action ([bold yellow]C[/]/[bold yellow]F[/]/[bold yellow]Q[/]): ").strip().lower()

        if action == 'q':
            console.print("[red]Exited pipeline. Progress saved in baseline files.[/]")
            client.unload_model()
            break
            
        elif action == 'c':
            user_focus = console.input("\nEnter focus area or custom guidelines (press Enter for auto-critique): ").strip()
            
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as prog:
                ref_task = prog.add_task(f"[cyan]Running Refinement Cycle {iteration}...[/]", total=None)
                
                # Context pruning: We only pass the current draft and user focus. 
                # This keeps token counts and VRAM consumption low.
                critic_refine_prompt = (
                    f"Critique the current design draft considering this custom focus: '{user_focus if user_focus else 'General Audit'}'\n\n"
                    f"Current Game Design Draft:\n{current_draft}"
                )
                
                critic_feedback = client.generate(critic_system, critic_refine_prompt, keep_alive="5m")
                
                architect_refine_prompt = (
                    f"Incorporate the Critic's audit and user guidelines into the design draft:\n"
                    f"User Guidelines: '{user_focus}'\n"
                    f"Critic Audit:\n{critic_feedback}\n\n"
                    f"Current Game Design Draft:\n{current_draft}"
                )
                
                updated_draft = client.generate(architect_system, architect_refine_prompt, keep_alive="5m")
                current_draft = updated_draft
                
                # Save intermediate refinement
                with open(os.path.join(args.output_dir, f"refinement_cycle_{iteration}_critic.md"), "w", encoding="utf-8") as f:
                    f.write(critic_feedback)
                with open(os.path.join(args.output_dir, f"refinement_cycle_{iteration}_architect.md"), "w", encoding="utf-8") as f:
                    f.write(updated_draft)
                
                prog.update(ref_task, completed=True, description=f"[green]Cycle {iteration} Complete![/]")
            
            console.print(Panel(
                Markdown(current_draft[:1500] + "\n\n... (Remainder truncated, view output/refinement files to read in full)"),
                title=f"Refinement Cycle {iteration} Draft Preview",
                border_style="yellow"
            ))
            iteration += 1

        elif action == 'f':
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as prog:
                f_task = prog.add_task("[cyan]Synthesizing final Game Design Document with Dopamine Audit...[/]", total=None)
                
                phase4_tmpl = load_prompt_file("prompts/phase4_instructions.txt")
                crit_inst_part = phase4_tmpl.split("[ARCHITECT INSTRUCTIONS]")[0].replace("[CRITIC INSTRUCTIONS]", "").strip()
                arch_inst_part = phase4_tmpl.split("[ARCHITECT INSTRUCTIONS]")[1].strip()

                # Generate Dopamine Audit
                crit_prompt = crit_inst_part.format(
                    phase3_architect=current_draft,
                    phase3_critic="Review the current refined draft mechanics"
                )
                dopamine_audit = client.generate(critic_system, crit_prompt, keep_alive="5m")
                
                with open(os.path.join(args.output_dir, "final_dopamine_audit.md"), "w", encoding="utf-8") as f:
                    f.write(dopamine_audit)

                # Final GDD Synthesis
                arch_prompt = arch_inst_part.format(
                    phase3_architect=current_draft,
                    phase3_critic="Synthesize the whole refined game loop"
                )
                arch_prompt += f"\n\nCritic's Dopamine & Retention Audit:\n{dopamine_audit}"
                
                # Final call sets keep_alive: 0 to free VRAM immediately
                final_gdd = client.generate(architect_system, arch_prompt, keep_alive="0")
                
                final_gdd_path = os.path.join(args.output_dir, "game_design_document.md")
                with open(final_gdd_path, "w", encoding="utf-8") as f:
                    f.write(final_gdd)
                    
                prog.update(f_task, completed=True, description="[green]Final Document Synthesized![/]")

            console.print("\n[bold green]Success! Game Design Deep Dive finished.[/]")
            console.print(f"Final Game Design Document generated at: [yellow]{final_gdd_path}[/]\n")

            console.print(Panel(
                Markdown(final_gdd[:1500] + "\n\n... (Remainder truncated, view output/game_design_document.md to read in full)"),
                title="Final GDD Preview",
                border_style="green"
            ))
            
            client.unload_model()
            break

if __name__ == "__main__":
    main()
