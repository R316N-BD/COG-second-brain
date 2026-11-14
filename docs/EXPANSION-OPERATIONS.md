# Nexus expansion: implementation and operating boundaries

Hermes owns bots/profiles, sessions, models, browser tool execution, Kanban/delegation, Cron, messaging, and its own approvals. COG owns the local vault, source provenance, MCP scope checks, local workflow history and research utilities. Nexus is a companion, not a second agent backend.

## Interactive preview

Open preview/nexus-expansion.html in a normal browser. This self-contained demonstration covers all twenty requested modules. No remote connections, shell, microphone, trading, or private vault reads. All sample agent states are synthetic. It is not the live Tkinter application. GitHub renders source; download the HTML to view it.

## Native operations

The existing Nexus launch command and Hermes MCP configuration are unchanged:

    .\scripts\start-nexus.ps1
    .\.venv\Scripts\python.exe -m cog_core hermes-config --profile hermes-research

Optional Windows tray and browser screenshots:

    .\.venv\Scripts\python.exe -m pip install -r requirements-nexus-desktop.txt
    .\.venv\Scripts\python.exe -m cog_core nexus

Click Tray + hotkey to opt in to system-wide Ctrl+Alt+Space and tray actions. It may fail if the shortcut is occupied or tray unsupported. Notification text contains no prompt/reply. Click Capture tab after attaching the dedicated browser. Playwright observes the last open tab, verifies its DevToolsActivePort identity, and saves a private PNG under runtime/screenshots. This is an on-demand snapshot, not a continuous cursor/video stream. Review and delete sensitive screenshots when appropriate. No ordinary browser profile, user login, or remote CDP endpoint is attached by this feature.

## Owner-only additional CLI

The add-ons are intentionally not MCP tools or remote commands.

    py -3.12 -m cog_core.nexus_addons model-route private --local-ready
    py -3.12 -m cog_core.nexus_addons aegis-summary "C:\path\audit.json"
    py -3.12 -m cog_core.nexus_addons skills
    py -3.12 -m cog_core.nexus_addons windows-launch notepad
    py -3.12 -m cog_core.nexus_addons home-state light.office --url http://127.0.0.1:8123

Model routes are recommendations only. The local-ready flag is operator-supplied; it is not proof that Ollama is available or offline. AEGIS summary returns only fixed event/severity categories and counts. No live stream or security enforcement. Home Assistant is a read of one entity through an explicitly configured loopback service or secure local tunnel, using a token prompted in the terminal; no device mutations. Windows launch requires the local operator to type exact confirmation and can launch only Calculator or Notepad from System32; no arbitrary UI automation, administrator elevation, shell, or agent control.

Optional local voice utilities:

    py -3.12 -m pip install faster-whisper
    py -3.12 -m cog_core.nexus_addons transcribe "C:\path\audio.wav" --model-dir "C:\models\local-whisper"
    py -3.12 -m pip install pywin32
    py -3.12 -m cog_core.nexus_addons speak "COG is ready."

Use an already-installed local Whisper model and trusted media files. CPU transcription, file input only, no microphone recording or wake word. The 10-minute transcript limit is not a hard decoder runtime or memory bound. Windows speech uses the installed SAPI voice. These optional dependencies and hardware paths need live platform testing.

## Knowledge and local workflows

See EXPANSION.md for workflow, extraction, backtest and semantic commands. Use explicitly chosen local-only Ollama, since a loopback endpoint alone does not prove local inference. The existing semantic index is owner-only and embeds a bounded first chunk; it does not expose agent-facing vector tools. Image OCR remains unimplemented. Document extraction is not a parser sandbox. Offline backtest is educational close-price research, not event-contract pricing, market monitoring, or live execution.

## Staged Windows source installer

Requires a Git checkout, reviewed full commit SHA, Git, Python 3.12, and permission to install optional dependencies. This is not a signed MSI/EXE.

    .\scripts\install-nexus-user.ps1 -Action Status
    .\scripts\install-nexus-user.ps1 -Action Install -Commit FULL_SHA -WithDesktopExtras -WithDocumentParsers -WhatIf
    .\scripts\install-nexus-user.ps1 -Action Install -Commit FULL_SHA -WithDesktopExtras -WithDocumentParsers
    .\scripts\install-nexus-user.ps1 -Action Launch
    .\scripts\install-nexus-user.ps1 -Action Activate -Commit PREVIOUS_READY_SHA

Replace FULL_SHA with a reviewed commit in the local checkout. Installation creates a distinct user-local release directory, exports tracked Git source, builds a venv at the final path, validates and then activates a pointer. An interrupted installation may leave an incomplete release; it is not activated. Existing ready releases and the separate private COG data directory are preserved. Activating a previous ready release rolls back application code only, not the user database or schema; back up data before switching. No automatic upstream download, signed verification, dependency lockfile or complete crash-safe updater is provided. Never install an unreviewed commit.

## Status by module

| Module | Actual scope | Remaining |
|---|---|---|
| Headquarters | Animated CSS 3D preview; live native 2D roster | Bind full 3D to Hermes activity |
| Floating | Existing panel plus optional tray/hotkey/notification code | Windows manual test, voice capture |
| Browser | Existing dedicated browser plus explicit Playwright capture | Live video, cursor mirroring, robust attach recovery |
| Computer | Owner-only fixed Windows application launch | Least-privilege app automation and action approvals |
| Voice | Optional local file transcription and SAPI TTS | Wake word, microphone and native Hermes voice integration |
| Memory | Existing FTS5 and opt-in scoped Ollama semantic index | Chunking, hybrid retrieval, policy-aware MCP exposure |
| Graph | Existing wiki-link graph and interactive demo | Live interactive graph with scoped results |
| Documents | TXT/MD/CSV, optional PDF/DOCX/XLSX | OCR, parser isolation and review workflow |
| Missions | Job records, local workflow run history | Native Hermes Kanban/delegation adapter, leases/reconciliation |
| Workflows | Validated local DAG execution, editable demo | Live visual editor and external approvals |
| Models | Hermes model configuration and local recommendations | Real measured model inventory, policy-enforced provider routing |
| AEGIS | Redacted offline event summary and existing COG audit | Live independent security integration |
| Studio | Existing GitHub metadata, editor/terminal mockup | Actual scoped editor/terminal and diffs |
| Bots | Live profile roster, source skill list | Authorized profile creation/updates in Hermes |
| Network | Architecture and preview | Remote authenticated gateways/worker enrollment |
| Android | Architecture and preview | Real Webapp/messaging link, native app optional |
| Home | Single read-only loopback entity adapter | Home Assistant MCP and approved writes |
| Trading | Offline historical CSV illustration | Validated market datasets and read-only live feeds |
| GenUI | Existing inert structured reply parser and expanded demo | Live composable application builder |
| Installer | Staged user-local PowerShell source installer | Windows manual validation, signed packages/updates/recovery |

Do not expose the local operator utilities to a restricted agent via shell. Application-level MCP scope checks are not OS isolation. No extra runtime or Hermes configuration was changed automatically.
