# Keystroke Dynamics

## Overview

Keystroke dynamics (also called typing biometrics) analyses the rhythm of a person's typing. The key insight is that everyone has a subtly unique typing pattern — even when typing the same phrase — shaped by their muscle memory, hand size, and habitual finger placement.

## What is measured

For each character in the phrase, two timing features are captured:

| Feature         | Description                                                              |
| --------------- | ------------------------------------------------------------------------ |
| **Dwell time**  | How long a key is held down (key-down to key-up), in milliseconds        |
| **Flight time** | The gap between releasing one key and pressing the next, in milliseconds |

## Enrolment

Students type the fixed phrase (default: `the quick brown fox`) the required number of times (default: 5). Each attempt produces a vector of dwell times and flight times for each character. The profile stores the **mean** and **standard deviation** of each feature across all attempts.

Features with low variance (consistent behaviour) contribute more to matching because a tight standard deviation narrows the expected range for that person.

## Identification

The system computes a **normalised Manhattan distance** between the sample and each stored profile. Distances are converted to confidence percentages using softmax with a configurable scale factor. See [How It Works](../algorithms.md#keystroke-mouse-dynamics) for the formula.

## Configuration

All settings are managed via the [Admin Panel](../admin.md#keystroke-dynamics) — no code changes required.

| Setting                         | Default               | Description                                                                                                                    |
| ------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **Typing phrase**               | `the quick brown fox` | The phrase typed during enrolment and identification. Changing it mid-session requires all students to re-enrol.               |
| **Enrolment attempts required** | `5`                   | Number of typing attempts required to build a profile                                                                          |
| **Confidence sensitivity**      | `2.0`                 | Softmax scale factor for converting distances to confidence percentages. Higher values sharpen the separation between matches. |

## Discussion points

- Ask students to type slowly versus quickly and observe how it affects the match score.
- What happens if the same person types on a different keyboard?
- How would you attack this system if you could observe someone typing?
