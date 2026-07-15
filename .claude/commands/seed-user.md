---
description: Create a single dummy user in the database
allowed-tools: Bash(venv\\Scripts\\python.exe scripts\\seed_user.py:*)
---

Run the reusable project CLI from the repository root:

```powershell
venv\Scripts\python.exe scripts\seed_user.py
```

This creates one randomly generated Indian user with a unique Gmail address and
the password `password123` stored as a Werkzeug hash.

For controlled test data, provide both details together:

```powershell
venv\Scripts\python.exe scripts\seed_user.py --name "Ananya Iyer" --email "ananya.iyer@example.com"
```

The command rejects duplicate email addresses and rejects calls that provide
only `--name` or only `--email`.
