# Autonomous Ops/Dev Agent with Real Guardrails
### A Self-Correcting Multi-Agent DevOps System with Live Guardrails & Real-Time Control Dashboard

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-FF6B35.svg)](https://github.com/langchain-ai/langgraph)
[![Docker](https://img.shields.io/badge/Docker-Sandbox_Execution-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📖 Overview

**Autonomous Ops/Dev Agent with Real Guardrails** is a next-generation AI-driven DevOps automation platform capable of accepting software issues, planning solutions, generating production-grade code, executing automated test suites in isolated sandboxes, independently reviewing code quality, and self-correcting failures before deployment.

It realizes the complete architectural blueprint specified in the academic synopsis (*Maharishi Markandeshwar University, 2026-27*) and synthesizes core design patterns from three state-of-the-art open-source software engineering repositories:
1. **[SWE-agent](https://github.com/SWE-agent/SWE-agent)**: Agent-Computer Interface (ACI) for surgical code editing, file navigation, lint feedback, and Git patch/PR workflows.
2. **[OpenHands](https://github.com/OpenHands/OpenHands)**: Event stream architecture, Docker container sandbox runtime, live WebSocket event broadcasting, and multi-layered guardrail interception.
3. **[multi-agent-coder](https://github.com/sriram369/multi-agent-coder)**: LangGraph conditional state machine, typed Pydantic state, specialized Planner/Coder/Tester/Critic agent roles, and automated self-correction loop.

---

## 🏗️ 6-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Presentation Layer: Real-Time Web Control Dashboard      │
│    (Live terminal stream, KPI cards, visual execution graph) │
├─────────────────────────────────────────────────────────────┤
│ 2. API Layer: FastAPI + Asynchronous WebSockets + JWT Auth   │
├─────────────────────────────────────────────────────────────┤
│ 3. Multi-Agent Layer: LangGraph Conditional State Machine   │
│    - Planner Agent    (Task decomposition & stack selection)│
│    - Coder Agent      (ACI file editing & Git commits)      │
│    - Tester Agent     (Pytest generation & sandbox test)    │
│    - Critic Agent     (Independent quality & security review│
│    - Escalation Agent (Safety thresholds & human-in-the-loop│
├─────────────────────────────────────────────────────────────┤
│ 4. Guardrail Layer: Live Security Engine                    │
│    - Prompt Injection Defense & Jailbreak Detection         │
│    - Shell Command Firewall (banned destructive commands)   │
│    - Python AST Static Security & Secret Leak Scanner       │
├─────────────────────────────────────────────────────────────┤
│ 5. Execution Layer: Sandboxed Execution                     │
│    - Docker Container Sandbox with CPU/Memory/Time limits   │
│    - Confined Subprocess Runner with working dir isolation   │
├─────────────────────────────────────────────────────────────┤
│ 6. Data Layer: SQLAlchemy ORM (10 Tables)                   │
│    - Users, Projects, Tasks, Agent Logs, Test Results,      │
│      Pull Requests, Docker Sessions, Audit Logs,            │
│      Notifications, Retry History                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart

### 1. Installation
```bash
git clone <repo-url>
cd Autonomous
python -m pip install -r requirements.txt
cp .env.example .env
```

### 2. Start the Real-Time Control Dashboard & Backend
```bash
python run_server.py
```
Open your browser at **`http://localhost:8000`** to access the Real-Time Control Dashboard.

### 3. Run directly from Terminal (CLI Mode)
```bash
python main.py "Build a REST API for a todo app with FastAPI and SQLite"
```

---

## 🧪 Testing

Run the automated test suite verifying guardrails, database models, and the full LangGraph pipeline:
```bash
pytest tests/ -v
```

---

## 🛡️ Guardrails & Safety
- **Prompt Injection Defense**: Intercepts prompt jailbreaks (DAN mode, system overrides, directive bypasses).
- **Command Firewall**: Blocks destructive bash commands (`rm -rf /`, `curl | bash`, reverse shells, `mkfs`).
- **AST Security Scanner**: Validates Python syntax, blocks dangerous imports (`ctypes`, `pty`), and scans for leaked API keys / credentials.
- **Human Escalation**: Automatically halts execution and alerts human developers if confidence drops below 75% or self-correction retries exceed limits.

---

## 📄 License
MIT License.
