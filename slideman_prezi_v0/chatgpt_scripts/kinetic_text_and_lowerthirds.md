# Kinetic Text & Lower‑Thirds Cue Sheet

## Global Style
- Font: Inter SemiBold, 64 px for primary bursts, 28 px for lower‑thirds.
- Colors: `#FFFFFF` on grad background, accent `#00E0FF` for key numbers.
- Animations use 8‑frame overshoot (Scale 1.2 → 1).

---

### Primary Kinetic Text Bursts

| Time | Text | Effect | Anchor |
|------|------|--------|--------|
| 00:08 | “€50 B productivity lost” | Characters drop from top staggered 2 f; bounce settling | Centre |
| 00:12 | “There has to be a better way.” | Fade‑in + 3 px wobble | Centre |
| 00:45 | “5 hours” (left) | Slide‑in from left, overshoot 1.05 | Left half |
| 00:46 | “5 minutes” (right) | Slide‑in from right, overshoot 1.05 | Right half |
| 01:24 | “Turn presentations into conversations” | Typewriter reveal, slight tracking‑in | Centre |

---

### Lower‑Third Captions (appear bottom‑left, stay 4 s)

| Time | Caption | Purpose |
|------|---------|---------|
| 00:18 | “Step 1 of 5 – Plan” | Clarify workflow |
| 00:27 | “Element‑level intelligence” | Feature call‑out |
| 00:51 | “+90 % faster · 0 errors” | Benefit highlight |
| 01:13 | “Join the wait‑list” | Reinforce CTA |

---

### Animation Specs

- **Slide‑in**: Start 120 px off‑screen, 0.4 s, cubic bezier (0.16, 1, 0.3, 1).
- **Bounce**: Scale 1.2 → 0.95 → 1 over 18 frames.
- **Typewriter**: 12 characters per 0.1 s, cursor blink after end.
- **Fade‑in**: Opacity 0 → 1 over 0.3 s with slight upward 16 px movement.

Implement in After Effects using the included motion presets folder (`/assets/aep/motion_presets.ffx`).
