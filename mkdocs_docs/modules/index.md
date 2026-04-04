# Modules

The Biometric Workshop Suite includes five independent biometric modules. Each module follows the same pattern: students **enrol** by performing the biometric action, then **identify** by performing it again — the system matches against all enrolled profiles and ranks them by confidence.

| Module | Technique | Matching |
|---|---|---|
| [Keystroke Dynamics](keystroke.md) | Typing rhythm | Normalised Manhattan distance |
| [Mouse Dynamics](mouse.md) | Pointer movement profiling | Normalised Manhattan distance |
| [Face Recognition](face.md) | Geometric facial landmarks | Cosine similarity |
| [Voice Biometrics](voice.md) | MFCC speaker features | Cosine similarity |
| [Signature Dynamics](signature.md) | On-screen stroke analysis | Weighted Euclidean distance |

See [How It Works](../algorithms.md) for a detailed breakdown of each matching algorithm.
