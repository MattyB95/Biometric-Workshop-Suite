# Face Recognition

## Overview

This module demonstrates geometric face recognition — a technique used in real-world systems such as passport e-gates and phone unlock. Rather than comparing raw pixels, the system extracts ratios between facial landmarks to produce a representation that is robust to lighting and scale changes.

## What is measured

A TinyFace model running entirely in the browser detects **68 facial landmarks**. From these, **16 normalised geometric ratios** are computed:

- Eye width relative to face width
- Nose length and width ratios
- Mouth width relative to face width
- Distances between eyes, nose, and mouth
- Jawline proportions

Normalising by face size makes the features independent of how close the student is to the camera.

## Enrolment

A single webcam capture is taken. The face model extracts the 16-element feature vector, which is stored directly as the profile. Because only one sample is taken, the enrolment process is fast but the profile has no variance information.

## Identification

Identification uses **cosine similarity** between the enrolment vector and the live capture vector. Similarities are normalised to confidence percentages. See [How It Works](../algorithms.md#face-recognition) for the formula.

## Requirements

- A webcam and browser permission to access it
- Reasonable front-facing lighting (avoid strong backlighting)
- The TinyFace model files must be served correctly — check the browser console for 404 errors if the model fails to load

## Discussion points

- Demonstrate how lighting changes affect the match score.
- Ask students: does the system recognise faces it has never seen? (No — it only ranks enrolled profiles.)
- What is the difference between *identification* (who is this?) and *verification* (is this person who they claim to be)?
- Why might geometric ratios be more robust than raw pixel comparison?
