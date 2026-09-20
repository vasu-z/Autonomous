"""
Direct Repository Importer & Bridge:
Imports and integrates actual code from the 3 cloned repositories:
1. external/multi_agent_coder
2. external/swe_agent
3. external/openhands
"""

import sys
from pathlib import Path

# Add external repositories to Python system path
BASE_DIR = Path(__file__).resolve().parent.parent
EXTERNAL_DIR = BASE_DIR / "external"

MAC_DIR = EXTERNAL_DIR / "multi_agent_coder"
SWE_DIR = EXTERNAL_DIR / "swe_agent"
OH_DIR = EXTERNAL_DIR / "openhands"

for p in [str(MAC_DIR), str(SWE_DIR), str(OH_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# 1. Direct Imports from sriram369/multi-agent-coder
try:
    from external.multi_agent_coder.prompts.system_prompts import (
        ARCHITECT_SYSTEM_PROMPT,
        CODER_SYSTEM_PROMPT,
        CODER_FIX_PROMPT,
        REVIEWER_SYSTEM_PROMPT,
        TESTER_SYSTEM_PROMPT,
    )
    from external.multi_agent_coder.agents.coder import parse_file_tags as mac_parse_file_tags
    HAS_MULTI_AGENT_CODER = True
except Exception as e:
    HAS_MULTI_AGENT_CODER = False
    print(f"[RepoImporter] Warning loading multi-agent-coder: {e}")

# 2. Direct Imports from SWE-agent/SWE-agent
try:
    from external.swe_agent.sweagent.tools.commands import (
        Command,
        ToolCall,
    )
    HAS_SWE_AGENT = True
except Exception as e:
    HAS_SWE_AGENT = False
    print(f"[RepoImporter] Warning loading swe-agent: {e}")

# 3. Direct Imports from OpenHands/OpenHands
try:
    from external.openhands.tools.canvas_ui_tool import (
        CanvasUIAction,
        CanvasUIObservation,
        CanvasCommand,
        CanvasTab,
    )
    HAS_OPENHANDS = True
except Exception as e:
    HAS_OPENHANDS = False
    print(f"[RepoImporter] Warning loading openhands: {e}")

def get_imported_status():
    return {
        "multi_agent_coder": HAS_MULTI_AGENT_CODER,
        "swe_agent": HAS_SWE_AGENT,
        "openhands": HAS_OPENHANDS
    }
