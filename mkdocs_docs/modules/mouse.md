# Mouse Dynamics

## Overview

Mouse dynamics analyses how a person moves and clicks a pointer. Movement speed, path shape, and click timing all vary between individuals and can form a behavioural fingerprint.

## What is measured

Students click through 8 on-screen targets in sequence. For each segment between targets, three features are captured:

| Feature | Description |
|---|---|
| **Movement time** | Time taken to move from one target to the next, in milliseconds |
| **Path curvature** | How curved the movement path is (ratio of arc length to straight-line distance) |
| **Click dwell** | How long the mouse button is held down on each target, in milliseconds |

## Enrolment

Students complete the 8-target sequence **5 times**. Each run produces a vector of movement times, curvatures, and click dwells. The profile stores the **mean** and **standard deviation** of each feature across all attempts.

## Identification

The system computes a **normalised Manhattan distance** between the sample and each stored profile, then converts distances to confidence percentages using softmax. See [How It Works](../algorithms.md#keystroke-mouse-dynamics) for the formula.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `MOUSE_ENROLL_SAMPLES_REQUIRED` | `5` | Number of enrolment runs required |

## Discussion points

- Try the module with a mouse vs. a trackpad — the profiles are noticeably different.
- How would the system perform if a user was tired or in a hurry?
- Could someone learn to mimic another person's mouse movement?
