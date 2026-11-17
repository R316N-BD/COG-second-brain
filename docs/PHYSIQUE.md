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

## Collaborative Coach Command — phase 2

- Create 4-agent team generates separate training, nutrition, recovery and research
  missions. Stage each into a fresh restricted Hermes session and manually import
  each returned draft. Keep responses concise (roughly 600–800 UTF-8 bytes each);
  combined reports plus review notes must fit the existing 6000-byte mission limit.
- Accept all four drafts, then select a team mission and create Safety review.
  Review the new safety draft separately; an accepted review does not establish safety.
- Only after accepting the safety review can Commander synthesis be generated.
  It uses accepted reports and review notes from the selected team only.
- Rejected reports block synthesis. Start a new team to revise; there is no
  automatic retry, agent provisioning, live parallel execution or independent
  enforcement of Hermes permissions. All prompts still require explicit Send.

## Body 3D — advanced educational explorer

The native Body 3D tab now has 30 named anatomical regions, original tessellated
ellipsoid meshes, orthographic 3D camera rotation, shading, front/back/side presets,
drag, tilt, zoom, surface/deep/all layers and region isolation. Click a visible
region or use the muscle dropdown. Each region includes a short action description.
Deep mode removes the base geometry to expose illustrative deeper regions.
It is not a scanned body, validated anatomical atlas, skin model, or a simulation
of muscle contractions, forces, joints or an individual's anatomy.

Select 7, 14, 30, 90 or 365 days. The exercise relationships tab lists recognized
primary and secondary exercises; training history shows recorded sets, repetitions,
external load and relationship, unique training dates, last mapped exposure and
the change from the preceding equal-length window. Heatmap colors represent
relative counts for the selected period, not biological activation, recovery,
injury risk or muscle growth. Teal indicates selection. Multiple regions may
share the same set; never sum regional counts to calculate total workout sets.
Left/right display is anatomical orientation only; the training log does not
record side-specific effort, so the display cannot infer asymmetry.

Exercise aliases are exact normalized matches. Custom movements without a mapping
are counted as unclassified, not automatically assigned. The existing broad
11-region API remains for compatibility; the detailed catalog has separate
associations. The viewer is local and read-only, and Lock clears its loaded history.

### Path to anatomical fidelity

Reference anatomy for future asset import:
- OpenStax Anatomy and Physiology 2e, chapter 11:
  https://openstax.org/books/anatomy-and-physiology-2e/pages/11-chapter-review
- BodyParts3D official dataset: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html
- BodyParts3D current license: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html
- Z-Anatomy model license: https://github.com/Z-Anatomy/Models-of-human-anatomy/blob/master/License.txt

No external meshes have been bundled. A future import should pin exact asset
versions, preserve attribution and license terms, validate anatomical IDs and
mesh coordinates, and provide an independent anatomical review before release.
The current 3D rendering is a stylized teaching model and has not been validated
by an anatomist. No pose detection, personalized scanning or joint mechanics yet.

## Mobile Athlete Command

Select Mobile, choose 1–365 days of check-ins/training history (default 90),
optionally include accepted commander reports from this session, and create
an encrypted HTML snapshot. It also includes the current contest target and
all milestones. Review the counts, unlock the vault, choose a separate
12+ character mobile passphrase, and select a new output file outside the
Git checkout. The file contains ciphertext, not plaintext athlete records.

Transfer the generated HTML privately to the phone, then open the trusted,
unmodified file locally in a browser with JavaScript and Web Crypto support.
Enter the mobile passphrase. Overview, Check-ins, Training, Prep and Feedback
are read-only. Lock clears displayed content; hiding the page also locks it.
The snapshot uses PBKDF2-SHA256 (600,000 iterations) and AES-256-GCM, no network
requests, and no localStorage. No passphrase is saved. Mobile browser file
opening and Web Crypto support vary; device testing remains required.
Do not upload snapshots to GitHub, email them as a matter of routine, or open
modified copies. A modified HTML file could steal the passphrase; CSP and
encryption do not protect against a malicious replacement or compromised OS.
Existing exports cannot be remotely revoked; delete old copies yourself.
No live sync, native APK, remote server, write-back or push notifications.
Snapshot encryption is distinct from the original Scrypt vault format.

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
- Anatomically detailed 3D mesh, local voice check-ins, native mobile application, live private sync and camera comparison.

All examples are synthetic. The public repository must never contain private data.
