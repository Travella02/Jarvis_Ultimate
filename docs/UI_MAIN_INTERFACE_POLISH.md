# UI Main Interface Polish

Version: 0.1.9

The native app shell is now structured around Jarvis as the main interface rather than a dashboard demo.

## Interface Zones

- **Left rail**: runtime status, voice controls, workspace panel list.
- **Core stage**: large living orb, state readout, and readiness strip.
- **Conversation dock**: primary text conversation area.
- **Diagnostics drawer**: collapsed-by-default debug/event stream.

## Visual State Intent

- `sleeping`: calm, dim, slow breathing.
- `wake_listening`: waiting for wake phrase.
- `listening`: active input pulse.
- `transcribing`: heard speech is being processed.
- `thinking`: faster ring/orbit motion.
- `speaking`: wave pulses around the orb.
- `working`: system calibration / warmup motion.
- `error`: alert color and shake.

## Design Direction

The UI should keep moving toward a dedicated Jarvis interface:

- fewer dashboard panels in the main view
- stronger focus on the orb
- smooth state motion
- conversation visible but not overpowering
- diagnostics available only when needed
