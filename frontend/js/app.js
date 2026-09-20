// Autonomous Ops/Dev Agent - Agent Canvas & SWE-agent Inspector Controller
document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const telemetryAgent = document.getElementById("telemetry-agent");
  const telemetryConfidence = document.getElementById("telemetry-confidence");
  const telemetryRetries = document.getElementById("telemetry-retries");
  const liveIndicator = document.getElementById("live-indicator");
  const liveText = document.getElementById("live-text");

  const chipArchitect = document.getElementById("chip-architect");
  const chipCoder = document.getElementById("chip-coder");
  const chipTester = document.getElementById("chip-tester");
  const chipCritic = document.getElementById("chip-critic");
  const chipEscalation = document.getElementById("chip-escalation");

  const taskInput = document.getElementById("task-input");
  const btnRunPipeline = document.getElementById("btn-run-pipeline");
  const taskStatusTag = document.getElementById("task-status-tag");
  const trajectoryStream = document.getElementById("trajectory-stream");

  const fileTreeList = document.getElementById("file-tree-list");
  const editorActiveFilename = document.getElementById("editor-active-filename");
  const editorCodeContainer = document.getElementById("editor-code-container");
  const btnCopyCode = document.getElementById("btn-copy-code");

  const terminalScreen = document.getElementById("terminal-screen");
  const termExitStatus = document.getElementById("term-exit-status");

  const diffContainer = document.getElementById("diff-container");
  const diffBranchName = document.getElementById("diff-branch-name");
  const prStatusBadge = document.getElementById("pr-status-badge");

  const testPassedVal = document.getElementById("test-passed-val");
  const testFailedVal = document.getElementById("test-failed-val");
  const testDurationVal = document.getElementById("test-duration-val");
  const testFullOutput = document.getElementById("test-full-output");

  let currentWorkspaceFiles = {};
  let activeSelectedFile = "app/main.py";
  let activeTaskId = null;

  // 1. Workbench Tab Switching
  document.querySelectorAll(".workbench-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".workbench-tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

      tab.classList.add("active");
      const targetPane = document.getElementById(tab.dataset.target);
      if (targetPane) targetPane.classList.add("active");
    });
  });

  // 2. Preset Task Pills
  document.querySelectorAll(".preset-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      taskInput.value = pill.dataset.task;
      taskInput.focus();
    });
  });

  // 3. Highlight Active Agent Chips
  function setActiveAgentChip(agentName) {
    [chipArchitect, chipCoder, chipTester, chipCritic, chipEscalation].forEach(c => c.classList.remove("active"));
    const name = (agentName || "").toLowerCase();

    if (name.includes("planner") || name.includes("architect")) chipArchitect.classList.add("active");
    else if (name.includes("coder")) chipCoder.classList.add("active");
    else if (name.includes("tester")) chipTester.classList.add("active");
    else if (name.includes("critic") || name.includes("reviewer")) chipCritic.classList.add("active");
    else if (name.includes("escalat")) chipEscalation.classList.add("active");
  }

  // 4. Append Trajectory Step Card
  function addTrajectoryCard(agentName, icon, title, content, meta = "") {
    const card = document.createElement("div");
    card.className = "trajectory-card";
    const time = meta || new Date().toLocaleTimeString();

    card.innerHTML = `
      <div class="card-header">
        <span class="agent-badge-label">
          <span>${icon}</span> ${agentName}: ${title}
        </span>
        <span class="card-meta-time">${time}</span>
      </div>
      <div class="card-body">${content}</div>
    `;
    trajectoryStream.appendChild(card);
    trajectoryStream.scrollTop = trajectoryStream.scrollHeight;
  }

  // 5. Append Line to Terminal
  function appendTerm(text, type = "info") {
    const line = document.createElement("div");
    line.className = `term-line ${type}`;
    line.textContent = text;
    terminalScreen.appendChild(line);
    terminalScreen.scrollTop = terminalScreen.scrollHeight;
  }

  // 6. Render File Tree & Code
  function renderFileTree(files) {
    currentWorkspaceFiles = files || {};
    fileTreeList.innerHTML = "";

    const fileNames = Object.keys(currentWorkspaceFiles);
    if (fileNames.length === 0) {
      fileTreeList.innerHTML = `<li style="padding: 0.5rem; color: var(--text-dim); font-size: 0.78rem;">No workspace files yet.</li>`;
      return;
    }

    fileNames.forEach((fname, idx) => {
      const li = document.createElement("li");
      li.className = `file-tree-item ${fname === activeSelectedFile || idx === 0 ? "selected" : ""}`;
      li.dataset.filename = fname;
      const icon = fname.includes("test") ? "🧪" : "📄";
      li.innerHTML = `<span>${icon}</span> ${fname}`;
      
      li.addEventListener("click", () => {
        document.querySelectorAll(".file-tree-item").forEach(item => item.classList.remove("selected"));
        li.classList.add("selected");
        displayCode(fname);
      });

      fileTreeList.appendChild(li);
    });

    if (fileNames.length > 0 && !currentWorkspaceFiles[activeSelectedFile]) {
      activeSelectedFile = fileNames[0];
    }
    displayCode(activeSelectedFile);
  }

  function displayCode(filename) {
    activeSelectedFile = filename;
    editorActiveFilename.textContent = filename;
    const content = currentWorkspaceFiles[filename] || "# Empty file";
    const lines = content.split("\n");

    editorCodeContainer.innerHTML = lines.map((line, idx) => `
      <div class="code-line">
        <span class="line-num">${idx + 1}</span>
        <span class="line-code">${escapeHtml(line)}</span>
      </div>
    `).join("");
  }

  // 7. Render Git Diff
  function renderDiff(diffText, branch = "devops-fix/task", prUrl = null) {
    diffBranchName.textContent = `Branch: ${branch}`;
    if (prUrl) {
      prStatusBadge.textContent = "PR Ready: #42";
      prStatusBadge.style.color = "var(--accent-emerald)";
    }

    if (!diffText || !diffText.trim()) {
      diffContainer.innerHTML = `<div style="padding: 1.5rem; color: var(--text-dim); font-family: var(--font-sans);">No uncommitted changes. All changes committed to branch.</div>`;
      return;
    }

    const lines = diffText.split("\n");
    diffContainer.innerHTML = lines.map(line => {
      let cls = "diff-info";
      if (line.startsWith("+") && !line.startsWith("+++")) cls = "diff-add";
      else if (line.startsWith("-") && !line.startsWith("---")) cls = "diff-del";
      return `<div class="diff-line ${cls}">${escapeHtml(line)}</div>`;
    }).join("");
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  // 8. Copy Code Handler
  btnCopyCode.addEventListener("click", () => {
    const code = currentWorkspaceFiles[activeSelectedFile] || "";
    navigator.clipboard.writeText(code).then(() => {
      btnCopyCode.textContent = "Copied!";
      setTimeout(() => btnCopyCode.textContent = "Copy Code", 1500);
    });
  });

  // 9. Launch Pipeline Action
  btnRunPipeline.addEventListener("click", async () => {
    const taskText = taskInput.value.trim();
    if (!taskText) {
      alert("Please enter a task description or pick a preset.");
      return;
    }

    try {
      btnRunPipeline.disabled = true;
      btnRunPipeline.innerHTML = "<span>⏳</span> Running...";
      taskStatusTag.textContent = "Executing";
      taskStatusTag.style.color = "var(--accent-cyan)";

      addTrajectoryCard("System", "⚡", "Pipeline Dispatched", `Task: "${taskText.slice(0, 100)}..."`);
      appendTerm(`[TASK DISPATCH] Starting autonomous execution for: ${taskText}`, "cmd");

      const res = await fetch("/api/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: taskText.slice(0, 50),
          description: taskText
        })
      });

      if (res.ok) {
        const data = await res.json();
        activeTaskId = data.task_id;
        pollTaskStatus(activeTaskId);
      } else {
        alert("Failed to start task.");
        btnRunPipeline.disabled = false;
        btnRunPipeline.innerHTML = "<span>🚀</span> Launch Pipeline";
      }
    } catch (e) {
      alert("Error: " + e.message);
      btnRunPipeline.disabled = false;
      btnRunPipeline.innerHTML = "<span>🚀</span> Launch Pipeline";
    }
  });

  // 10. Poll Task Status & Update Workbench
  let pollInterval = null;
  function pollTaskStatus(taskId) {
    if (pollInterval) clearInterval(pollInterval);

    pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/tasks/${taskId}`);
        if (!res.ok) return;

        const task = await res.json();
        telemetryAgent.textContent = task.current_agent || "Executing";
        telemetryConfidence.textContent = `${(task.confidence_score * 100).toFixed(0)}%`;
        telemetryRetries.textContent = `${task.retry_count} / 2`;
        setActiveAgentChip(task.current_agent);

        if (task.status === "COMPLETED" || task.status === "ESCALATED" || task.status === "FAILED") {
          clearInterval(pollInterval);
          btnRunPipeline.disabled = false;
          btnRunPipeline.innerHTML = "<span>🚀</span> Launch Pipeline";
          taskStatusTag.textContent = task.status;
          taskStatusTag.style.color = task.status === "COMPLETED" ? "var(--accent-emerald)" : "var(--accent-rose)";

          addTrajectoryCard(
            task.current_agent || "Critic",
            task.status === "COMPLETED" ? "✔" : "⚠️",
            `Execution ${task.status}`,
            `Status: <strong>${task.status}</strong> &middot; Confidence: ${(task.confidence_score*100).toFixed(0)}% &middot; Retries: ${task.retry_count}`
          );

          // Fetch final files and diff
          fetchTaskFiles(taskId);
          fetchTaskDiff(taskId);

          if (task.test_results && task.test_results.length > 0) {
            const tr = task.test_results[task.test_results.length - 1];
            testPassedVal.textContent = tr.passed_count;
            testFailedVal.textContent = tr.failed_count;
            testFullOutput.textContent = tr.test_output || "All tests passed successfully.";
            appendTerm(tr.test_output, "success");
          }
        }
      } catch (e) {
        console.error("Poll error", e);
      }
    }, 1500);
  }

  async function fetchTaskFiles(taskId) {
    try {
      const res = await fetch(`/api/tasks/${taskId}/files`);
      if (res.ok) {
        const data = await res.json();
        renderFileTree(data.files);
      }
    } catch (e) {}
  }

  async function fetchTaskDiff(taskId) {
    try {
      const res = await fetch(`/api/tasks/${taskId}/diff`);
      if (res.ok) {
        const data = await res.json();
        renderDiff(data.diff, data.branch, data.pr_url);
      }
    } catch (e) {}
  }

  // 11. WebSocket Setup
  function initWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onopen = () => {
      liveText.textContent = "Live Connected";
      liveIndicator.style.borderColor = "rgba(16, 185, 129, 0.25)";
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.event === "agent_status") {
          telemetryAgent.textContent = msg.data.agent;
          setActiveAgentChip(msg.data.agent);
          addTrajectoryCard(msg.data.agent, "⚡", msg.data.status, msg.data.message);
          appendTerm(`[${msg.data.agent}] ${msg.data.message}`, "info");
        }
      } catch (e) {}
    };

    ws.onclose = () => {
      liveText.textContent = "Reconnecting...";
      setTimeout(initWebSocket, 3000);
    };
  }

  initWebSocket();

  // Load existing recent task if available
  fetch("/api/tasks")
    .then(r => r.json())
    .then(tasks => {
      if (tasks && tasks.length > 0) {
        const latest = tasks[0];
        fetchTaskFiles(latest.id);
        fetchTaskDiff(latest.id);
      }
    });
});
