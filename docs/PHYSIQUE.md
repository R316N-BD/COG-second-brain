# COG Physique 2.0 — local bodybuilding workspace

This optional Nexus division uses Hermes-first design but introduces no second runtime.
The current MVP is owner-operated; Hermes, MCP, general memory, cloud models and
external coaches cannot access the vault through any new tool.

## Browser design preview

Open [preview/physique.html](../preview/physique.html) locally in a browser. The preview uses synthetic data and never saves anything or contacts Hermes. It is not the native encrypted vault UI.

## Run
From the feature checkout, initialize COG if needed:
```powershell
py -3.12 -m cog_core init
py -3.12 -m pip install -r requirements-physique.txt
py -3.12 -m cog_core physique
```
Or open Nexus and select **Physique**. Linux: replace `py -3.12` with `python3`
and install the system Tk package if required.

Create the vault with a unique passphrase. Record optional weight (kg), sleep,
training minutes and self-reported adherence. Use a contest target date and
review the last 7 days versus the preceding 7 days, including sample counts.
Missing values are not treated as zero. Replace and delete are explicit operations.
The module is single-owner, not a multi-athlete service.

## Native 2.0 workspace
- Command: contest countdown, 7-day means, 30-day weight chart and period comparisons.
- Check-ins: add, explicitly replace, and delete daily records.
- Training log: date, exercise, reps, external load in kg, optional RPE, weekly sets/session dates and load-volume (reps × external load; not a physiological workload score).
- Personal bests: heaviest recorded set per exercise, ties resolved by reps; not estimated 1RM.
- Prep planner: owner-entered contest date and milestones, completion toggles and overdue count.
- Privacy: display lock clears charts, tables and input fields; no background agent access.

Version 1 ciphertext is read and migrated in memory; the next successful write saves the v2 schema. Back up the encrypted file first. Version 1 software cannot read migrated v2 records. The desktop uses kg; the browser preview is illustrative.

## AI Coach Command — phase 1

Open the AI Coach tab. Seven role-specific mission templates are included.
The queue, prompts and pasted replies are session-only; closing or locking the
workspace clears them locally. It does not recall anything previously staged
or sent. No athlete record is automatically read, attached, stored or shared.

1. Choose a role and enter a non-sensitive mission topic.
2. Create the mission and inspect its exact prompt.
3. From Nexus, connect the existing authenticated Hermes loopback dashboard,
   select a trusted restricted profile and choose New session. Stage in Nexus
   copies the draft into an empty composer only; it does not send.
4. Review the selected profile, provider, existing configuration and exact
   outgoing text (Nexus may append its optional rich-response instructions).
   Press Send yourself. Standalone Physique supports manual copying instead.
5. Paste the returned text into Returned draft, then Save pasted reply.
6. Accept or reject with a review note. Acceptance records a review decision
   only; it never executes a recommendation or updates athlete records.

Each role is a prompt template, not a provisioned Hermes bot. For independent
review, select a different restricted Hermes profile and use a new session.
Do not assume separate sessions imply separate models or safety guarantees.
The prompt's restrictions are advisory, not a sandbox: configure Hermes
without filesystem, shell, browser, MCP or other action permissions for these
profiles. Research missions should use supplied public sources; the current
templates do not authorize tools to independently verify citations.
Hermes may retain messages or send them to its configured model provider;
never enter private health records or identifiers. No automatic retries,
multi-agent dispatch, durable mission persistence, direct response import,
or runtime permission enforcement is implemented.

## Tests
`python -m unittest discover -s tests -p 'test_physique*.py' -v` after installing the optional dependency. GUI rendering and OS-level security need manual testing.

## Privacy
Records live outside the framework checkout at `physique/records.enc` under the
configured COG data directory. Scrypt derives a key; AES-256-GCM authenticates and
encrypts the full state with fresh salt and nonce each write. The passphrase is
never saved. Writes use a temporary encrypted file and an exclusive lock; a crash
may require manual lock recovery after confirming no writer is active. Losing the
passphrase means losing access. No recovery key is implemented. Back up ciphertext
manually to a trusted location; verify restoration separately. OS account security,
screen privacy, malware protection and full-disk encryption remain necessary.
The module is not clinically validated, independently audited, HIPAA-certified,
multi-tenant, or resistant to a compromised local machine. Summary output is
visible to the owner; avoid sharing terminal output or screenshots.

No clinical documents, photos, compound/dose logs or medical records are supported. Exercise and milestone labels accept short text; avoid identifying or sensitive information. Never commit real athlete
data. The general COG index and MCP should not ingest this directory.

## Next phases (not implemented)
- Detailed nutrition history and opt-in data import.
- Coach Brain: approved methodology with cited evidence, review before sharing,
  prompt-injection controls, explicit scoped retrieval and no implicit cloud calls.
- Research agent: sources, publication date, evidence type and limitations.
- Posing Studio: local landmark extraction and coach-reviewed visual feedback;
  no inferred body fat, diagnoses or judging guarantees.
- Health vault: separately authorized lab imports, verified units/reference ranges,
  clinician review, private exposure journal only after threat modeling.
  No dosing, cycle design or automated medical guidance.
- Recovery and prep: descriptive trends and clinician/coach-approved workflows;
  no rapid dehydration or extreme weight-loss recommendations.
- Hermes specialist profile provisioning and scoped, explicitly approved summaries; provenance, independent review and durable missions.
- Multi-athlete CRM: isolated tenants, role-based controls, consent/revocation,
  access audit, export/deletion, billing and independent security review.
- AEGIS integration: redacted event categories without biomarker or athlete data.
- Anatomy explorer, local voice check-ins, mobile UI, and camera comparison.

All examples are synthetic. The public repository must never contain private data.
