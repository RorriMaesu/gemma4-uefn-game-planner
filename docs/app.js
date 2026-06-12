// App State Control
const API_BASE = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") ? "" : "http://127.0.0.1:8000";
let pollInterval = null;
let lastLogsLength = 0;
let hasAttemptedAutoLaunch = false;

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initTerminalToggle();
    initActionHandlers();
    startStatusPolling();
});

// 1. Tab Handlers
function initTabs() {
    const tabButtons = document.querySelectorAll(".tab-btn");
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            const target = btn.getAttribute("data-tab");
            document.querySelectorAll(".tab-pane").forEach(pane => {
                pane.classList.remove("active");
            });
            document.getElementById(target).classList.add("active");
        });
    });
}

// 2. Terminal Toggle
function initTerminalToggle() {
    const header = document.getElementById("terminal-header");
    const drawer = document.getElementById("terminal-drawer");
    const btn = document.getElementById("btn-toggle-terminal");
    
    header.addEventListener("click", () => {
        drawer.classList.toggle("expanded");
        btn.textContent = drawer.classList.contains("expanded") ? "▼" : "▲";
    });
}

// 3. Action Handlers
function initActionHandlers() {
    const btnStart = document.getElementById("btn-start");
    const btnRefine = document.getElementById("btn-refine");
    const btnFinalize = document.getElementById("btn-finalize");
    const btnUnload = document.getElementById("btn-unload-vram");
    const btnDownload = document.getElementById("btn-download-gdd");
    const copyButtons = document.querySelectorAll(".copy-btn");
    const btnAbort = document.getElementById("btn-abort");

    // Start baseline plan
    btnStart.addEventListener("click", () => {
        const concept = document.getElementById("game-concept").value.stripOrEmpty();
        if (!concept) {
            alert("Please enter a game concept first.");
            return;
        }

        btnStart.disabled = true;
        btnStart.textContent = "Processing...";
        appendLog("[System] Initiating baseline game design...", "system");

        fetch(`${API_BASE}/api/start`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ concept: concept })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "started") {
                appendLog("[System] Pipeline thread successfully started.", "success");
            } else {
                appendLog("[Error] Failed to start pipeline: " + data.message, "error");
                btnStart.disabled = false;
                btnStart.textContent = "Generate Baseline Plan";
            }
        })
        .catch(err => {
            appendLog("[Error] Network error during start: " + err, "error");
            btnStart.disabled = false;
            btnStart.textContent = "Generate Baseline Plan";
        });
    });

    // Abort active generation
    btnAbort.addEventListener("click", () => {
        if (!confirm("Are you sure you want to abort the current generation session?")) {
            return;
        }
        btnAbort.disabled = true;
        btnAbort.textContent = "Aborting...";
        appendLog("[System] Sending abort request to backend...", "system");
        
        fetch(`${API_BASE}/api/abort`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            appendLog("[System] Abort request completed.", "success");
            btnAbort.disabled = false;
            btnAbort.textContent = "Abort / Reset";
        })
        .catch(err => {
            appendLog("[Error] Failed to abort: " + err, "error");
            btnAbort.disabled = false;
            btnAbort.textContent = "Abort / Reset";
        });
    });

    // Submit Refinement Round
    btnRefine.addEventListener("click", () => {
        const focusText = document.getElementById("refinement-focus").value;
        appendLog(`[Input] Submitting refinement cycle focus: "${focusText || 'None'}"`, "input");
        sendAction("C", focusText);
    });

    // Finalize Game Design
    btnFinalize.addEventListener("click", () => {
        appendLog("[System] Compiling final Game Design Document...", "system");
        sendAction("F");
    });

    // Manual Unload VRAM
    btnUnload.addEventListener("click", () => {
        appendLog("[System] Triggering manual VRAM model unload...", "system");
        fetch(`${API_BASE}/api/vram/unload`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            appendLog("[System] Unload command complete.", "success");
        });
    });

    // Toggle Autopilot
    const btnToggleAutopilot = document.getElementById("btn-toggle-autopilot");
    btnToggleAutopilot.addEventListener("click", () => {
        const isCurrentlyActive = btnToggleAutopilot.textContent.includes("Pause");
        const newState = !isCurrentlyActive;
        
        appendLog(`[System] Toggling autopilot to: ${newState ? "Enabled" : "Paused"}`, "system");
        
        fetch(`${API_BASE}/api/autopilot/toggle`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ enable: newState })
        })
        .then(res => res.json())
        .then(data => {
            appendLog(`[System] Autopilot successfully ${newState ? "started" : "paused"}.`, "success");
        })
        .catch(err => {
            appendLog(`[Error] Failed to toggle autopilot: ${err}`, "error");
        });
    });

    // Download compiled GDD
    btnDownload.addEventListener("click", () => {
        fetch(`${API_BASE}/api/status`)
        .then(res => res.json())
        .then(data => {
            if (data.final_gdd) {
                const blob = new Blob([data.final_gdd], { type: "text/markdown" });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "game_design_document.md";
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            }
        });
    });

    // Brainstorm Preset Click Handling
    const presetButtons = document.querySelectorAll(".preset-btn");
    presetButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const presetText = btn.getAttribute("data-preset");
            const focusArea = document.getElementById("refinement-focus");
            focusArea.value = presetText;
            appendLog(`[System] Loaded preset: "${btn.innerText}"`, "system");
            
            focusArea.focus();
            document.getElementById("refinement-panel").scrollIntoView({ behavior: "smooth" });
        });
    });

    // Copy viewer content to clipboard
    copyButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetId = btn.getAttribute("data-target");
            const viewer = document.getElementById(targetId);
            
            // Extract code text or innerText
            const textToCopy = viewer.innerText;
            navigator.clipboard.writeText(textToCopy)
            .then(() => {
                const originalText = btn.textContent;
                btn.textContent = "Copied!";
                btn.classList.add("btn-success");
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.classList.remove("btn-success");
                }, 1500);
            })
            .catch(err => {
                alert("Failed to copy text: " + err);
            });
        });
    });
}

// 4. Status Polling
function startStatusPolling() {
    pollInterval = setInterval(() => {
        fetch(`${API_BASE}/api/status`)
        .then(res => res.json())
        .then(status => {
            // Remove offline warning if present
            const warning = document.getElementById("launcher-offline-warning");
            if (warning) warning.remove();
            const launcherCard = document.getElementById("launcher-card");
            if (launcherCard) {
                launcherCard.style.border = "1px solid rgba(59, 130, 246, 0.3)";
                launcherCard.style.background = "rgba(59, 130, 246, 0.05)";
            }
            updateUI(status);
        })
        .catch(err => {
            console.error("Error polling state status: ", err);
            
            // Show dynamic offline warning on launcher card
            const launcherCard = document.getElementById("launcher-card");
            if (launcherCard) {
                launcherCard.style.border = "2px solid rgba(239, 68, 68, 0.6)";
                launcherCard.style.background = "rgba(239, 68, 68, 0.08)";
                let warning = document.getElementById("launcher-offline-warning");
                if (!warning) {
                    warning = document.createElement("div");
                    warning.id = "launcher-offline-warning";
                    warning.style.color = "var(--accent-red)";
                    warning.style.fontWeight = "600";
                    warning.style.marginBottom = "12px";
                    warning.style.fontSize = "0.95rem";
                    warning.style.padding = "8px 12px";
                    warning.style.borderRadius = "6px";
                    warning.style.background = "rgba(239, 68, 68, 0.15)";
                    warning.style.border = "1px solid rgba(239, 68, 68, 0.2)";
                    warning.innerHTML = "⚠️ Local backend server is offline. Please extract the downloaded ZIP and run <code>launcher.bat</code> to initialize the app and register auto-launch.";
                    launcherCard.insertBefore(warning, launcherCard.firstChild);
                }
            }

            // Auto-launch the local setup tool if the local server is offline
            if (!hasAttemptedAutoLaunch && !sessionStorage.getItem("autoLaunched")) {
                hasAttemptedAutoLaunch = true;
                sessionStorage.setItem("autoLaunched", "true");
                console.log("[System] Local server offline. Triggering custom protocol launcher...");
                window.location.href = "ollama-planner://launch";
            }
        });
    }, 450);
}

// Helper to sanitize/strip whitespace
String.prototype.stripOrEmpty = function() {
    return this.trim();
};

// 5. Update GUI Elements based on backend state
function updateUI(status) {
    // A. Update VRAM indicator
    const vramBadge = document.getElementById("vram-badge");
    vramBadge.textContent = status.vram_status;
    if (status.vram_status.toLowerCase() === "active") {
        vramBadge.className = "status-badge state-active";
    } else {
        vramBadge.className = "status-badge state-unloaded";
    }

    // A2. Update Autopilot indicators in header
    const autopilotBadge = document.getElementById("autopilot-badge");
    const btnToggleAutopilot = document.getElementById("btn-toggle-autopilot");
    if (autopilotBadge && btnToggleAutopilot) {
        if (status.autopilot) {
            autopilotBadge.textContent = "Active";
            autopilotBadge.className = "status-badge state-active";
            btnToggleAutopilot.textContent = "Pause Autopilot";
        } else {
            autopilotBadge.textContent = "Paused";
            autopilotBadge.className = "status-badge state-unloaded";
            btnToggleAutopilot.textContent = "Start Autopilot";
        }
    }

    // B. Update Timeline Progress active class
    const steps = ["step-phase1", "step-phase2", "step-phase3", "step-refine", "step-phase4"];
    steps.forEach(id => document.getElementById(id).className = "timeline-step");

    if (status.phase === "phase1") {
        document.getElementById("step-phase1").className = "timeline-step active";
    } else if (status.phase === "phase2") {
        document.getElementById("step-phase1").className = "timeline-step completed";
        document.getElementById("step-phase2").className = "timeline-step active";
    } else if (status.phase === "phase3") {
        document.getElementById("step-phase1").className = "timeline-step completed";
        document.getElementById("step-phase2").className = "timeline-step completed";
        document.getElementById("step-phase3").className = "timeline-step active";
    } else if (status.phase === "refinement") {
        document.getElementById("step-phase1").className = "timeline-step completed";
        document.getElementById("step-phase2").className = "timeline-step completed";
        document.getElementById("step-phase3").className = "timeline-step completed";
        document.getElementById("step-refine").className = "timeline-step active";
    } else if (status.phase === "phase4") {
        document.getElementById("step-phase1").className = "timeline-step completed";
        document.getElementById("step-phase2").className = "timeline-step completed";
        document.getElementById("step-phase3").className = "timeline-step completed";
        document.getElementById("step-refine").className = "timeline-step completed";
        document.getElementById("step-phase4").className = "timeline-step active";
    } else if (status.phase === "finished") {
        steps.forEach(id => document.getElementById(id).className = "timeline-step completed");
    }

    // C. Render Design Viewer Tabs
    renderMarkdown("architect-viewer", status.architect_content, "Start generation to see architect layout.");
    renderMarkdown("critic-viewer", status.critic_content, "Reviews will appear side-by-side with architectural files.");

    // D. Refinement input panel display
    const refPanel = document.getElementById("refinement-panel");
    if (status.phase === "refinement" || status.is_waiting) {
        refPanel.style.display = "block";
        const badge = refPanel.querySelector(".badge");
        const desc = refPanel.querySelector(".refinement-desc");
        if (badge && desc) {
            if (status.autopilot) {
                badge.textContent = "Autopilot Active";
                badge.className = "badge badge-glow-active animate-pulse";
                desc.textContent = "Autopilot Active: Reviewing and critiquing. Enter focus guidelines below to inject custom focus into the next loop cycle, or click Finalize to compile the complete game design document.";
            } else {
                badge.textContent = "Action Required";
                badge.className = "badge badge-glow animate-pulse";
                desc.textContent = "Manual Mode: Review the baseline or current draft tabs above. Enter focus guidelines to refine the design, or click Finalize to compile the complete game design document.";
            }
        }
    } else {
        refPanel.style.display = "none";
    }

    // E. Handle final GDD synthesis completion
    const btnStart = document.getElementById("btn-start");
    const gddTabBtn = document.getElementById("tab-gdd-btn");
    const btnAbort = document.getElementById("btn-abort");

    // Toggle start/abort buttons visibility based on phase
    if (status.phase === "idle" || status.phase === "finished") {
        if (btnAbort) btnAbort.style.display = "none";
        btnStart.disabled = false;
        btnStart.textContent = "Generate Baseline Plan";
    } else {
        if (btnAbort) btnAbort.style.display = "inline-flex";
        btnStart.disabled = true;
        btnStart.textContent = "Generating...";
    }

    if (status.phase === "finished" && status.final_gdd) {
        if (gddTabBtn.style.display !== "block") {
            gddTabBtn.style.display = "block";
            gddTabBtn.click();
        }
        renderMarkdown("gdd-viewer", status.final_gdd, "");
    } else {
        gddTabBtn.style.display = "none";
    }

    // F. Append logs
    if (status.logs && status.logs.length > lastLogsLength) {
        const newLogs = status.logs.slice(lastLogsLength);
        newLogs.forEach(line => {
            let type = "info";
            if (line.includes("[Error]") || line.includes("Error connecting")) type = "error";
            else if (line.includes("[System]")) type = "system";
            else if (line.includes("Success!")) type = "success";
            else if (line.includes("[Input]")) type = "input";
            appendLog(line, type);
        });
        lastLogsLength = status.logs.length;
    }
}

// 6. Parse and Render Markdown with Smart Scroll and LaTeX math protection
function renderMarkdown(elementId, markdownText, placeholderText) {
    const viewer = document.getElementById(elementId);
    if (!markdownText || markdownText.trim() === "") {
        viewer.innerHTML = `<div class="empty-state"><p>${placeholderText}</p></div>`;
        return;
    }

    // Extract math blocks to avoid marked.js parsing errors (e.g. underscores parsed as <em>)
    const mathBlocks = [];
    let processedText = markdownText;

    // 1. Extract block-level math: $$ ... $$
    processedText = processedText.replace(/\$\$([\s\S]+?)\$\$/g, (match) => {
        const placeholder = `%%DISPLAY_MATH_${mathBlocks.length}%%`;
        mathBlocks.push({
            placeholder: placeholder,
            original: match
        });
        return placeholder;
    });

    // 2. Extract inline math: $ ... $
    processedText = processedText.replace(/\$([^\$\s](?:[^\$]*?[^\$\s])?)\$/g, (match) => {
        const placeholder = `%%INLINE_MATH_${mathBlocks.length}%%`;
        mathBlocks.push({
            placeholder: placeholder,
            original: match
        });
        return placeholder;
    });

    // 3. Parse Markdown using marked.js
    let parsedHTML = marked.parse(processedText);

    // 4. Restore original math blocks into the parsed HTML
    mathBlocks.forEach(item => {
        parsedHTML = parsedHTML.replace(item.placeholder, item.original);
    });

    if (viewer.innerHTML !== parsedHTML) {
        // Only auto-scroll if user is near the bottom (prevents hijacking if they scroll up to read)
        const isNearBottom = (viewer.scrollHeight - viewer.clientHeight - viewer.scrollTop) < 100;
        
        viewer.innerHTML = parsedHTML;
        
        // Render math equations with KaTeX if available
        if (typeof renderMathInElement === "function") {
            try {
                renderMathInElement(viewer, {
                    delimiters: [
                        {left: "$$", right: "$$", display: true},
                        {left: "$", right: "$", display: false},
                        {left: "\\(", right: "\\)", display: false},
                        {left: "\\[", right: "\\]", display: true}
                    ],
                    throwOnError: false
                });
            } catch (e) {
                console.error("KaTeX rendering error: ", e);
            }
        }
        
        if (isNearBottom) {
            viewer.scrollTop = viewer.scrollHeight;
        }
    }
}

// 7. Write line to floating console terminal drawer
function appendLog(line, type = "info") {
    const logsContainer = document.getElementById("console-logs");
    const lineEl = document.createElement("span");
    lineEl.className = `log-line ${type}`;
    lineEl.textContent = line;
    logsContainer.appendChild(lineEl);
    
    // Auto Scroll
    const body = document.getElementById("terminal-body");
    body.scrollTop = body.scrollHeight;
}

// 8. Submit Refinement/Finalize input action
function sendAction(actionVal, focusVal = "") {
    fetch(`${API_BASE}/api/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: actionVal, focus: focusVal })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "ok") {
            appendLog("[System] Action successfully registered.", "success");
            // Clear input
            document.getElementById("refinement-focus").value = "";
        } else {
            appendLog("[Error] Failed to send action: " + data.message, "error");
        }
    })
    .catch(err => {
        appendLog("[Error] Network error during action: " + err, "error");
    });
}
