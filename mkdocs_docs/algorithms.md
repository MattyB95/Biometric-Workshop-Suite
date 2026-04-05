# How It Works

## Keystroke & Mouse Dynamics

### Building a profile

During enrolment, each attempt produces a feature vector. After all required samples are collected, the profile stores the **mean** and **standard deviation** of each feature across attempts:

```
mean[i]  = average of feature i across all enrolment samples
std[i]   = standard deviation of feature i across all enrolment samples
```

### Matching: normalised Manhattan distance

For a new sample, the distance to a stored profile is:

```
distance = mean over all features of  |sample[i] − mean[i]| / max(std[i], floor)
```

The `floor` prevents division by near-zero standard deviations when a feature is very consistent:

| Modality            | Floor values |
| ------------------- | ------------ |
| Keystroke dwell     | 15 ms        |
| Keystroke flight    | 25 ms        |
| Mouse movement time | 30 ms        |
| Mouse click dwell   | 15 ms        |
| Mouse curvature     | 0.03         |

**Why this works:** features with low variance (consistent behaviour) have a small `std`, so even a small deviation produces a large normalised distance. Consistent features are effectively weighted more heavily.

### Converting distances to confidence

Distances are converted to confidence percentages using **softmax**:

```
confidence[i] = exp(−distance[i]) / sum(exp(−distance[j]) for all j)
```

The negative sign means smaller distances → higher confidence. The softmax ensures all confidences sum to 100%.

---

## Face Recognition

### Feature extraction

A TinyFace model detects 68 facial landmarks. 16 geometric ratios are computed from these landmarks (eye widths, nose proportions, mouth width, inter-feature distances), all normalised by face size to remove scale dependence.

### Matching: cosine similarity

The similarity between an enrolment vector **e** and a sample vector **s** is:

```
similarity = (e · s) / (|e| × |s|)
```

A similarity of 1.0 means the vectors point in exactly the same direction (identical features). A similarity of 0.0 means they are orthogonal (completely different).

Similarities are normalised so they sum to 100% confidence across all enrolled profiles.

---

## Voice Biometrics

### Feature extraction

The browser records audio and computes a short-time Fourier transform (STFT) to produce a spectrogram. From the spectrogram, **Mel-Frequency Cepstral Coefficients (MFCCs)** are extracted per frame — 13 coefficients capturing the spectral envelope of the voice.

The enrolment profile is the **mean MFCC vector** across all frames of the recording.

### Matching: cosine similarity

Identification uses the same cosine similarity formula as face recognition, applied to the 13-element MFCC vectors.

---

## Signature Dynamics

### Feature extraction

Six scalar features are extracted from the stroke data:

| Feature               | How computed                                                                         |
| --------------------- | ------------------------------------------------------------------------------------ |
| Duration              | `end_time − start_time` in seconds                                                   |
| Path length           | Sum of Euclidean distances between consecutive points, normalised by canvas diagonal |
| Average velocity      | `path_length / duration`                                                             |
| Peak velocity         | Maximum instantaneous speed between consecutive points                               |
| Stroke count          | Number of pen-down events (mouse/touch down without up)                              |
| Direction-change rate | Count of direction reversals per second of drawing time                              |

### Matching: weighted Euclidean distance

Features are normalised per dimension, then combined:

```
distance = sqrt( sum over all features of  w[i] × ((sample[i] − profile[i]) / scale[i])² )
```

where `scale[i]` is a per-feature normalisation constant tuned to the expected range of each measurement, and `w[i]` is a feature weight (all currently equal). Distances are converted to confidence using softmax.
