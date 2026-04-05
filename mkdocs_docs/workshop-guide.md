# Running a Workshop Session

## Before students arrive

1. Start the server on the presenter's machine (`just run` or `just run-network`).
2. Connect all student devices to the same network and point browsers at `http://<your-ip>:5000`.
   - Or use a single shared computer and take turns.
3. Navigate to **Instructor Admin** on the home page, enter the admin PIN (default: `1965`), and reset any profiles left from a previous session.

---

## General pattern for each module

1. Each student enters their name and **enrols** by performing the biometric action (typing, moving the mouse, speaking, etc.).
2. Once several students are enrolled, any student can press **Identify** — the system ranks all profiles by confidence and shows the best match.
3. Discuss the results as a group (see discussion prompts below).

---

## Module notes

### Keystroke Dynamics

- Students type the configured phrase (default: `the quick brown fox`) the required number of times (default: **5**) to build their profile. Encourage natural, consistent typing speed.
- The fixed phrase keeps all profiles comparable. Changing it mid-session requires re-enrolling everyone.
- The phrase, enrolment count, and confidence sensitivity can all be adjusted in the [Admin Panel](admin.md#keystroke-dynamics) without restarting the server.

### Mouse Dynamics

- Students click through **8 on-screen targets** the required number of times (default: **5**). Movement paths are visualised live.
- Results vary noticeably between a mouse and a trackpad — worth demonstrating to the group.
- Enrolment attempts and confidence sensitivity are adjustable in the [Admin Panel](admin.md#mouse-dynamics).

### Face Recognition

- Requires webcam access. One capture per student (single-sample enrolment).
- Uses facial geometry (ratios between landmarks), not pixel comparison — lighting affects results.
- Works best with consistent, front-facing positioning and even lighting.

### Voice Biometrics

- Students speak into the microphone for the configured duration (default: **10 seconds**) to enrol. A second recording is used for identification.
- Results are affected by background noise, microphone quality, and speaking style.
- Encourage students to speak naturally and at a consistent distance from the microphone.
- Recording duration can be adjusted in the [Admin Panel](admin.md#voice-biometrics) (range: 3–60 seconds).

### Signature Dynamics

- Students draw their signature on screen using a mouse, trackpad, or touchscreen the required number of times (default: **3**). Progress dots show how many samples remain.
- The features from all samples are averaged into a single profile — more attempts produce a more stable profile.
- The system measures _how_ the signature is drawn (speed, stroke count, direction changes), not just its shape.
- Encourage students to sign as they naturally would — not to draw slowly and carefully.
- Enrolment attempts can be adjusted in the [Admin Panel](admin.md#signature-dynamics).

---

## Discussion prompts

- Why does the system sometimes get it right / wrong?
- Which module felt most reliable? Why?
- What would an attacker need to do to fool each system?
- How do these techniques differ from passwords or PINs?
- What are the privacy implications of storing biometric data?
- Where are these techniques used in the real world?
- What happens to accuracy when more people enrol?

---

## Troubleshooting

| Problem                                               | Solution                                                                                           |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Wrong key resets the keystroke attempt                | Type carefully — the phrase must be typed exactly as shown                                         |
| Keystroke/mouse results always favour the same person | Ensure at least 3–4 students have enrolled before identifying                                      |
| Identification seems random                           | Try enrolling with more consistent speed and technique                                             |
| Server not reachable from other devices               | Use `just run-network` or ensure `host="0.0.0.0"` in `src/app.py`                                  |
| Camera not working (Face module)                      | Check browser permissions — the page needs webcam access                                           |
| Microphone not working (Voice module)                 | Check browser permissions and ensure no other app holds the mic                                    |
| Face model fails to load                              | Model files in `static/models/` must be accessible — check browser console for 404 errors          |
| Admin PIN forgotten                                   | Delete `admin_config.json` from the project root; the default PIN `1965` is restored on next start |
