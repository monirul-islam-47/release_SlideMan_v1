# Packaging & CI Highlights
- PyInstaller spec beside pyproject.toml → dist/PPTX‑Manager EXE (Windows‑first).

- CI (.github/workflows/ci.yml) matrix pinned to Python 3.9:
lint → unit tests → pytest‑qt → PyInstaller build.

- Self‑update (MVP): helper that fetches latest GitHub Release asset, verifies checksum, swaps EXE, and restarts.

# Key Conventions
1. "Services without Qt" rule – Keeps COM/SQL logic independent & testable.

2. src/ import root – Works out‑of‑box with IDEs and PyInstaller (--paths src).

3.Resources via .qrc – One compiled resources_rc.py; switching themes is just loading a different .qss.

4.Undo/Redo encapsulated – Every edit action lives in its own QUndoCommand subclass for easy rollback and future versioning.

Feel free to rename folders, but keep the separation between ui ⇔ services ⇔ models and the top‑level src/, resources/, tests/ pattern—it scales cleanly as features (AI tagging, cloud sync) arrive in v2.