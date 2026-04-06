# Voice Biometrics

## Overview

Voice biometrics (speaker recognition) identifies a person by the unique characteristics of their voice — shaped by the size and shape of their vocal tract, learned speech patterns, and accent. This module demonstrates the standard MFCC-based approach used in telephone banking and smart speaker authentication.

## What is measured

The browser records a short audio clip and performs short-time Fourier analysis to produce a **spectrogram**. From the spectrogram, **Mel-Frequency Cepstral Coefficients (MFCCs)** are extracted per frame:

| Feature         | Description                                                            |
| --------------- | ---------------------------------------------------------------------- |
| **MFCC vector** | 13 coefficients per frame capturing the spectral envelope of the voice |
| **Mean MFCC**   | The mean across all frames — forms the enrolment profile               |
| **Pitch**       | Fundamental frequency estimate, displayed for visualisation            |

MFCCs approximate how the human auditory system perceives sound, making them effective for speaker characterisation.

## Enrolment

The student makes the configured number of recordings (default: 3) each lasting the configured duration (default: 10 seconds). After each recording the page shows progress dots and prompts for the next attempt. Once all recordings are collected, the mean MFCC vector from each is averaged into a single representative profile.

## Identification

A second recording of the same duration is taken. Its mean MFCC vector is compared against all enrolled profiles using **cosine similarity**. Similarities are normalised to confidence percentages. See [How It Works](../algorithms.md#voice-biometrics) for the formula.

## Configuration

All settings are managed via the [Admin Panel](../admin.md#voice-biometrics) — no code changes required.

| Setting                         | Default | Description                                                                                                                                                     |
| ------------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Recording duration**          | `10 s`  | How many seconds of audio are captured per recording. Range: 3–60 seconds. Longer recordings produce a more stable MFCC profile but take more time per student. |
| **Enrolment attempts required** | `3`     | How many voice recordings to collect during enrolment. Each recording's mean MFCC is averaged with the others to form the final profile. Range: 1–10.           |

## Requirements

- A microphone and browser permission to access it
- A reasonably quiet environment — background noise degrades accuracy significantly

## Discussion points

- Ask students to try different voices (whisper, high pitch) and observe the match score.
- What environmental factors degrade voice recognition?
- Where is voice biometrics used commercially? (Phone banking, Alexa voice profiles, etc.)
- What is a "replay attack" and how would you defend against it?
