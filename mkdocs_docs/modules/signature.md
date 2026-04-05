# Signature Dynamics

## Overview

Signature dynamics (also called dynamic signature verification) analyses _how_ a signature is produced, not just what it looks like. Unlike a static image comparison, this approach captures the pen movement over time — making it far harder to forge.

## What is measured

Students draw their signature on a canvas element using a mouse, trackpad, or touchscreen. Six scalar features are extracted from the stroke data:

| Feature                   | Description                                                               |
| ------------------------- | ------------------------------------------------------------------------- |
| **Duration**              | Total time to complete the signature, in seconds                          |
| **Path length**           | Total distance travelled by the pointer, normalised by canvas size        |
| **Average velocity**      | Mean speed of the stroke throughout the signature                         |
| **Peak velocity**         | Maximum instantaneous speed recorded                                      |
| **Stroke count**          | Number of distinct pen-down strokes (pen lifts)                           |
| **Direction-change rate** | Frequency of direction changes — captures the angularity of the signature |

## Enrolment

Students draw their signature the required number of times (default: 3). After each sample the page shows progress dots and prompts for the next attempt. Once all samples are collected, the six features from each attempt are **averaged** into a single representative profile. This multi-sample approach smooths out minor within-session variability.

## Identification

A new signature is drawn and its feature vector is compared against all enrolled profiles using a **weighted Euclidean distance** normalised per feature. Distances are converted to confidence percentages. See [How It Works](../algorithms.md#signature-dynamics) for the formula.

## Configuration

All settings are managed via the [Admin Panel](../admin.md#signature-dynamics) — no code changes required.

| Setting                         | Default | Description                                                                                                                            |
| ------------------------------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **Enrolment attempts required** | `3`     | Number of signature samples collected during enrolment. Each attempt is extracted separately and then averaged into the final profile. |

## Discussion points

- Ask a student to try signing very slowly vs. at their natural pace — does it still match?
- Can a student successfully forge another student's signature on screen? What makes it difficult?
- How does this differ from a static image comparison (e.g. scanning a paper signature)?
- What features would you add to make this more robust?
