# Keystroke Dynamics Demo

A biometric authentication demo for workshops and classroom use. Students enrol their typing rhythm, then the system identifies who is typing based on their unique keystroke patterns — no passwords required.

---

## What is Keystroke Dynamics?

Every person types differently. Even when typing the same phrase, people vary in:

- **Dwell time** — how long each key is held down
- **Flight time** — the gap between releasing one key and pressing the next

These tiny timing differences form a biometric "fingerprint" of how you type. This demo captures those timings, builds a profile per student, and uses them to identify the typist.

---

## Features

- **Enrol** — students type a fixed phrase 5 times to build their profile
- **Identify** — type the phrase once and see ranked confidence scores for all enrolled students
- **Students** — view, delete, or reset enrolled profiles
- Works in any modern web browser
- Three hosting options: run locally, deploy to GitHub Pages, or host on Render

---

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

---

## Quick Start

**1. Clone the repository**

```bash
git clone <repo-url>
cd Keystroke-Dynamics-Demo
```

**2. Install dependencies**

```bash
uv sync
```

**3. Run the server**

```bash
uv run python app.py
```

**4. Open your browser**

```
http://localhost:5000
```

---

## Running a Workshop Session

### Setup (before students arrive)

1. Start the server on the presenter's machine.
2. Connect all student devices to the same network and point browsers at `http://<your-ip>:5000`.
   - Or use a single shared computer and take turns.
3. If restarting from a previous session, go to the **Students** tab and click **Reset All Profiles**.

### Step 1 — Enrol each student

1. Open the **Enrol** tab.
2. Enter the student's first name and click **Start Typing**.
3. Type `the quick brown fox` exactly as shown — 5 times in a row.
4. Each correct completion fills in a dot. The profile saves automatically after the 5th attempt.
5. Repeat for every student (click **Enrol Another Student** between each one).

> **Tip:** Tell students to type naturally and at their normal speed. Deliberately slow or exaggerated typing makes the profile less reliable.

### Step 2 — Identify who is typing

1. Open the **Identify** tab (or pass the keyboard to a student without telling anyone else who it is).
2. Type `the quick brown fox`.
3. The results panel shows every enrolled student ranked by confidence, with animated bars.

### Step 3 — Discuss the results

- Why does the system get it right/wrong?
- What happens if you type unusually slowly?
- How is this different from a password?
- Where is keystroke dynamics used in the real world?

---

## How the Matching Works

### Enrolment

For each of the 5 typing attempts, the app records:
- One **dwell time** per character (key-down → key-up, in milliseconds)
- One **flight time** per adjacent character pair (key-up[i] → key-down[i+1])

After all attempts, it calculates the **mean** and **standard deviation** of each timing feature and stores them in `profiles.json`.

### Identification

When a new sample arrives, the app computes a **normalised Manhattan distance** to every stored profile:

```
distance = average over all features of  |sample - mean| / max(std, floor)
```

Features where a student is very consistent (low std) are weighted more heavily. The distances are then passed through a **softmax** to produce confidence percentages that sum to 100%.

---

## Configuration

Open `app.py` and edit the constants near the top:

| Variable | Default | Description |
|---|---|---|
| `PHRASE` | `"the quick brown fox"` | The phrase everyone types |
| `ENROLL_SAMPLES_REQUIRED` | `5` | Number of enrolment attempts required |

> Keep the phrase the same for everyone in a session. If you change it mid-session, delete `profiles.json` and re-enrol all students.

---

## Hosting Options

### Option A — GitHub Pages (static, no server needed)

The `docs/` folder contains a fully self-contained version of the app with all logic in JavaScript and profiles stored in the browser's `localStorage`.

1. Push the repository to GitHub.
2. Go to **Settings → Pages** and set the source to **Deploy from a branch**, branch `main`, folder `/docs`.
3. Your app will be live at `https://<username>.github.io/<repo-name>/`.

> **Note:** Profiles are stored in the browser only. All students must use the same browser on the same device, or use the **Export / Import** feature on the Students tab to transfer profiles between browsers.

The static version also supports changing the typing phrase and enrolment sample count from the **Students → Settings** panel, without editing any code.

---

### Option B — Render (hosted Flask app, shared across devices)

The Flask version supports multiple devices simultaneously — ideal if students each have their own laptop or tablet.

1. Push the repository to GitHub.
2. Sign up at [render.com](https://render.com) and click **New → Web Service**.
3. Connect your GitHub repository. Render will detect `render.yaml` automatically and configure everything.
4. Click **Deploy**. Your app will be live at `https://keystroke-dynamics-demo.onrender.com` (or similar).
5. Share the URL with your students.

> **Note:** Render's free tier spins down after 15 minutes of inactivity. The first request after a sleep may take ~30 seconds. Profiles are stored in `profiles.json` on the server's disk and will be reset when the service redeploys.

To run in production mode locally (mirrors Render):
```bash
just serve
```

---

### Option C — Local network (no deployment required)

```bash
just run-network
```

Then share your machine's local IP (e.g. `http://192.168.1.42:5000`) with students on the same WiFi. No accounts or deployment needed.

---

## Project Structure

```
.
├── app.py               # Flask backend — routes and matching algorithm
├── templates/
│   └── index.html       # Frontend for the Flask version
├── docs/
│   └── index.html       # Standalone static version (GitHub Pages)
├── render.yaml          # Render deployment config (Option B)
├── justfile             # Task runner shortcuts
├── profiles.json        # Created automatically on first enrolment (Flask version)
├── pyproject.toml       # Project metadata and dependencies
└── README.md
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Wrong key resets the attempt | Type carefully — the system requires the exact phrase |
| Results always show the same person | Make sure at least 3–4 students have enrolled |
| Identification seems random | Try enrolling with more consistent typing speed |
| Server not reachable from other devices | Run with `app.run(host="0.0.0.0", port=5000)` in `app.py` |
