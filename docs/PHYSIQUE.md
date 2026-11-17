# COG Physique — local bodybuilding workspace

This optional Nexus division uses Hermes-first design but introduces no second runtime.
The current MVP is owner-operated; Hermes, MCP, general memory, cloud models and
external coaches cannot access the vault through any new tool.

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

No patient identifiers, clinical documents, photos, compound/dose logs, free text,
or medical records are accepted in this first version. Never commit real athlete
data. The general COG index and MCP should not ingest this directory.

## Next phases (not implemented)
- Training set/exercise log and nutrition adherence, with opt-in data import.
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
- Hermes specialist profiles: explicit opt-in, least-privilege access to approved
  summaries only, provenance and human approval before athlete-facing output.
- Multi-athlete CRM: isolated tenants, role-based controls, consent/revocation,
  access audit, export/deletion, billing and independent security review.
- AEGIS integration: redacted event categories without biomarker or athlete data.
- Anatomy explorer, local voice check-ins, mobile UI, and camera comparison.

All examples are synthetic. The public repository must never contain private data.
