# Deployment

There are three ways to run the Biometric Workshop Suite.

---

## Option A — GitHub Pages (static, no server needed)

The `docs/` folder is a fully self-contained static version — all logic runs in JavaScript and all profiles are stored in the browser's `localStorage`. No Python or server required.

1. Push the repository to GitHub.
2. Go to **Settings → Pages**, set source to **Deploy from a branch**, branch `main`, folder `/docs`.
3. Your suite will be live at `https://<username>.github.io/<repo-name>/`.

!!! note
    In the static version, each student's data is stored in *their own browser*. The admin page on the static version can only manage data on the device where it is opened. For a shared server where all students connect to the same backend, use Option B or C.

---

## Option B — Render (hosted Flask app, shared across devices)

The Flask version stores all profiles on the server — all students share the same profile store in real time. Ideal when students each have their own device.

1. Push the repository to GitHub.
2. Sign up at [render.com](https://render.com) and click **New → Web Service**.
3. Connect your repository. Render will detect `render.yaml` and configure everything automatically.
4. Click **Deploy** and share the URL with students.

!!! note
    Render's free tier spins down after 15 minutes of inactivity — the first request after a sleep may take ~30 seconds. Profile data stored on disk will be reset on each redeploy.

To run in production mode locally (mirrors the Render environment):

```bash
just serve
```

---

## Option C — Local network (no deployment required)

The simplest option for a classroom: run the server on the presenter's machine and share the local IP address.

```bash
just run-network
```

Then share `http://<your-local-ip>:5000` with students on the same Wi-Fi. No accounts, deployment, or internet connection needed.

---

## Environment configuration

Open `src/app.py` and edit the constants near the top:

| Variable | Default | Description |
|---|---|---|
| `PHRASE` | `"the quick brown fox"` | The phrase typed in the Keystroke module |
| `ENROLL_SAMPLES_REQUIRED` | `5` | Keystroke enrolment attempts required |
| `MOUSE_ENROLL_SAMPLES_REQUIRED` | `5` | Mouse enrolment attempts required |
| `DEFAULT_ADMIN_PIN` | `"1965"` | Fallback PIN if `admin_config.json` is absent |

The admin PIN can also be changed at runtime via the [Admin Panel](admin.md) without restarting the server.

---

## Data files

The Flask app auto-creates these files in the project root on first use:

| File | Contents |
|---|---|
| `profiles.json` | Keystroke profiles |
| `mouse_profiles.json` | Mouse dynamics profiles |
| `face_profiles.json` | Face recognition profiles |
| `voice_profiles.json` | Voice biometric profiles |
| `signature_profiles.json` | Signature dynamics profiles |
| `admin_config.json` | Admin PIN |

All files are plain JSON. They are listed in `.gitignore` to avoid accidentally committing student data.
