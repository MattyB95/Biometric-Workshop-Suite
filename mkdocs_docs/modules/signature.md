# Signature Dynamics

## Overview

Signature dynamics (also called dynamic signature verification) analyses *how* a signature is produced, not just what it looks like. Unlike a static image comparison, this approach captures the pen movement over time — making it far harder to forge.

## What is measured

Students draw their signature on a canvas element using a mouse, trackpad, or touchscreen. Six scalar features are extracted from the stroke data:

| Feature | Description |
|---|---|
| **Duration** | Total time to complete the signature, in seconds |
| **Path length** | Total distance travelled by the pointer, normalised by canvas size |
| **Average velocity** | Mean speed of the stroke throughout the signature |
| **Peak velocity** | Maximum instantaneous speed recorded |
| **Stroke count** | Number of distinct pen-down strokes (pen lifts) |
| **Direction-change rate** | Frequency of direction changes — captures the angularity of the signature |

## Enrolment

A single signature is captured and the six features are computed and stored as the profile.

## Identification

A second signature is drawn. Its feature vector is compared against all enrolled profiles using a **weighted Euclidean distance** normalised per feature. Distances are converted to confidence percentages. See [How It Works](../algorithms.md#signature-dynamics) for the formula.

## Discussion points

- Ask a student to try signing very slowly vs. at their natural pace — does it still match?
- Can a student successfully forge another student's signature on screen? What makes it difficult?
- How does this differ from a static image comparison (e.g. scanning a paper signature)?
- What features would you add to make this more robust?
