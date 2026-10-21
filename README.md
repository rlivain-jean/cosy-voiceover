# cosy-voiceover

Google Chirp 3 HD voiceovers for Cosyworld videos. Same voices as the YouTube ads (narrator: Charon, character: Puck).

- Put a script in `scripts/<name>.json` and push; the `voiceover` workflow writes `audio/<name>/<line-id>.wav` (48 kHz mono) and commits it.
- Only changed lines are re-synthesised (see `audio/<name>/manifest.json`).
- The key lives **only** in the Actions secret `GOOGLE_TTS_KEY` (Settings > Secrets and variables > Actions). It never sits on a computer or in the repo.
