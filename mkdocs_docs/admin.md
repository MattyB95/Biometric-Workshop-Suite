# Admin Panel

The admin panel is a PIN-protected page for instructors to manage enrolled profiles during a workshop. It prevents students from accidentally or deliberately deleting each other's data.

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
- **Change the admin PIN**

## Changing the PIN

Use the **Change Admin PIN** form at the bottom of the admin page. The new PIN must be at least 4 characters. The change takes effect immediately and is persisted to `admin_config.json` — the server does not need to be restarted.

If the PIN is forgotten, delete `admin_config.json` from the project root. The default PIN `1965` will be restored on the next server start.

## Flask vs static version

| Version                    | How auth works                                               | Scope                                          |
| -------------------------- | ------------------------------------------------------------ | ---------------------------------------------- |
| Flask app (`/admin`)       | Server-side session; PIN checked against `admin_config.json` | All connected students share one profile store |
| Static site (`admin.html`) | Client-side PIN check; PIN stored in `localStorage`          | Only manages data on the **current device**    |

In the static version, each student's data is stored in their own browser's `localStorage`. The static admin page can only manage profiles on the device it is opened on.

## Security note

The admin PIN is a convenience measure to prevent accidental profile deletion during a workshop — it is not a security control. The PIN is stored in plain text in `admin_config.json` and the check is simple string equality. Do not rely on this for any real access control. See [SECURITY.md](https://github.com/MattyB95/Biometric-Workshop-Suite/blob/main/SECURITY.md) for the full scope of intentional limitations.
