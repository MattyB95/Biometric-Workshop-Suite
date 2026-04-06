# Admin Panel

The admin panel is a PIN-protected page for instructors to manage enrolled profiles and configure module settings during a workshop. It prevents students from accidentally or deliberately deleting each other's data or changing session parameters.

## Accessing the admin panel

Navigate to `/admin` from the home page (or click the **Instructor Admin** link). You will be prompted for the admin PIN before any management actions are available.

**Default PIN: `1965`**

## What you can do

From the admin panel, an instructor can:

- **View** all enrolled profiles for every modality, including the number of enrolment samples stored
- **Delete** an individual profile by name
- **Reset** all profiles for a specific modality (clean slate for that module)
- **Reset all** profiles across all five modalities at once
- **Export** profiles for any modality as a JSON file (useful for saving a session or backing up data)
- **Import** profiles from a previously exported JSON file (merges with any existing profiles)
- **Configure per-modality settings** without editing code (see [Settings](#settings) below)
- **Change the admin PIN**

## Settings

The **Settings** section lets instructors tune each module's behaviour for the session. All changes take effect immediately — no server restart required. Settings are persisted to `admin_config.json` (Flask) or `localStorage` (static site) and survive page reloads.

### Keystroke Dynamics

| Setting                         | Default               | Description                                                                                                                                               |
| ------------------------------- | --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Typing phrase**               | `the quick brown fox` | The phrase students type during enrolment and identification. Changing it mid-session requires all students to re-enrol.                                  |
| **Enrolment attempts required** | `5`                   | How many times a student must type the phrase to build their profile. More attempts produce a more stable profile.                                        |
| **Confidence sensitivity**      | `2.0`                 | Softmax scale factor applied when converting distances to confidence percentages. Higher values sharpen the separation between close and distant matches. |

### Mouse Dynamics

| Setting                         | Default | Description                                                                                             |
| ------------------------------- | ------- | ------------------------------------------------------------------------------------------------------- |
| **Enrolment attempts required** | `5`     | How many times a student must complete the target-clicking sequence to build their profile.             |
| **Confidence sensitivity**      | `2.0`   | Softmax scale factor. Higher values increase the confidence gap between the best and second-best match. |

### Voice Biometrics

| Setting                         | Default | Description                                                                                                                                                                                                                                              |
| ------------------------------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Recording duration**          | `10 s`  | How many seconds of audio are captured for each enrolment or identification recording. Range: 3–60 seconds. Longer recordings produce a more representative MFCC profile but take more time.                                                             |
| **Enrolment attempts required** | `3`     | How many voice recordings a student must make during enrolment. Each recording's mean MFCC vector is extracted, then all are averaged into a single representative profile. More attempts improve stability at the cost of additional time. Range: 1–10. |

### Signature Dynamics

| Setting                         | Default | Description                                                                                                                                                                                                        |
| ------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Enrolment attempts required** | `3`     | How many signatures a student must draw during enrolment. Each sample's features are extracted separately, then averaged into a single representative profile. More samples smooth out within-session variability. |

## Changing the PIN

Use the **Change Admin PIN** form at the bottom of the admin page. The new PIN must be at least 4 characters. The change takes effect immediately and is persisted to `admin_config.json` — the server does not need to be restarted.

If the PIN is forgotten, delete `admin_config.json` from the project root. The default PIN `1965` will be restored on the next server start.

## Flask vs static version

| Version                    | How auth works                                                      | Scope                                                       |
| -------------------------- | ------------------------------------------------------------------- | ----------------------------------------------------------- |
| Flask app (`/admin`)       | Server-side session; PIN and settings stored in `admin_config.json` | All connected students share one profile store and settings |
| Static site (`admin.html`) | Client-side PIN check; PIN and settings stored in `localStorage`    | Only manages data on the **current device**                 |

In the static version, each student's data is stored in their own browser's `localStorage`. The static admin page can only manage profiles and settings on the device it is opened on.

## Security note

The admin PIN is a convenience measure to prevent accidental profile deletion or configuration changes during a workshop — it is not a security control. The PIN is stored in plain text in `admin_config.json` and the check is simple string equality. Do not rely on this for any real access control. See [SECURITY.md](https://github.com/MattyB95/Biometric-Workshop-Suite/blob/main/SECURITY.md) for the full scope of intentional limitations.
