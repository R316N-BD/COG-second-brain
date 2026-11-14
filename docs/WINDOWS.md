# COG native Windows foundation

Requires Windows PowerShell 5.1 or later, Python 3.10+ (3.12 recommended), and Git for update previews. No Bash, WSL, administrator permissions, or Python package installation is required for the native core.

From PowerShell in the framework checkout:

    .\scripts\setup-windows.ps1
    .\scripts\cog-doctor.ps1
    .\scripts\cog.ps1 validate
    .\scripts\cog-update.ps1 -Offline

If local script execution is blocked by policy, review the scripts and use the direct Python commands instead:

    py -3 -m cog_core validate
    py -3 -m cog_core init
    py -3 -m cog_core doctor
    py -3 -m cog_core update-preview --offline

The setup initializes %LOCALAPPDATA%\COG\vault, memory, logs, config, backups and runtime. A custom location can be specified using -DataDir on setup/doctor or --data-dir before the Python subcommand. The location must be outside Git working trees. Setup never overwrites an existing configuration or imports your notes.

The doctor checks executable discovery (Git, Hermes and Ollama) and validates the shipped skill catalog. Discovery is not a connectivity or authentication test. It does not modify Hermes settings or start services.

The original skills still expect their original vault-relative paths. This release creates the separate vault but does not automatically route existing skills to it. Do not assume opening the public framework in Obsidian is private. Open the new vault for notes; the Hermes/Codex skill adapter and safe migration are next.

Update preview reports cached or remote upstream commit IDs without fetching or changing files. Native update application, encrypted backups, runtime permissions, memory indexing, scheduled tasks and the desktop GUI are not implemented yet. Existing Bash scripts remain available on compatible systems.

Run native tests with:

    py -3 -m unittest discover -s tests -p test_native_core.py -v
