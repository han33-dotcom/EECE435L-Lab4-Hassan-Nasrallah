# School Management System — EECE435L Lab 4

Student: Hassan Nasrallah  
Course: EECE435L Software Tools Laboratory  
Work mode: Solo

This repository brings the Tkinter and PyQt5 interfaces from the earlier labs into one project. Both interfaces use the same object model and SQLite repository, so records created in one interface are available when the other interface is opened. The Tkinter source includes the Sphinx documentation added in Lab 3.

## Files

- `part1_oop.py` — students, instructors, courses, validation, JSON, CSV, and search.
- `part2_tkinter.py` — Tkinter desktop interface.
- `part3_pyqt5.py` — PyQt5 desktop interface.
- `part4_database.py` — SQLite persistence, backup, and restore.
- `test_lab2.py` — automated tests for the shared model and persistence.
- `docs/` — Sphinx source for both interfaces.

## Install and run

Use Python 3.10 or later. From this repository directory:

```powershell
python -m pip install -r requirements.txt
python part2_tkinter.py
```

To use the PyQt5 interface instead, close Tkinter and run:

```powershell
python part3_pyqt5.py
```

Both commands read and write `school_management.db` in the current directory. The first launch creates a small demonstration dataset. Use only one interface at a time so an older in-memory view cannot overwrite changes made by the other. For a fresh demo, either interface also accepts `--demo`. Use `--database PATH` to choose a different SQLite file.

Both interfaces support managing students, instructors, and courses, searching, JSON import/export, saving and loading the SQLite database, and making database backups. The PyQt5 interface also provides CSV export. The shared model and database logic provide the integration between the two GUIs.

## Verify

```powershell
python -m unittest -v test_lab2.py
```

The tests use temporary files, so they do not change the application's database.

## Build API documentation

```powershell
python -m pip install -r requirements-docs.txt
sphinx-build -b html docs docs/_build/html
```

Open `docs/_build/html/index.html` after the build. The documentation source is tracked; generated HTML is excluded from Git.

## Git workflow

This is a solo project, so the Lab 4 handout's two-person branch, pull request, and contribution-tracking steps do not apply. The repository history records the shared backend, both GUIs, and documentation in separate commits. The final version is tagged `v1.0`.
