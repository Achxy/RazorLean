# RazorProof video production plan

## Format

- Delivery: 1920×1080, 30 fps, H.264 high profile, AAC 48 kHz.
- Master: ProRes 422 or DNxHR HQ if storage permits.
- Runtime: target 4:57; hard ceiling 5:00.
- Spoken pace: 138–145 words per minute, with deliberate silence in the cold open.
- Captions: burned-in only for critical phrases; attach full subtitle track separately if the submission platform allows it.
- Safe area: keep essential text inside the central 90% width and 90% height.

## Recording order

1. Record narration as a scratch track.
2. Cut a radio edit to 4:50–4:55 before filming.
3. Render Manim scenes against the scratch timing.
4. Record the dashboard demo using the final cursor path.
5. Film notebook overhead shots.
6. Film A-roll last, after the wording and pauses are internalized.
7. Replace scratch narration only where A-roll does not carry the line.
8. Mix, caption, inspect at 1× and 1.5×, then export.

This order avoids filming a beautiful five-minute monologue that cannot accommodate the demo.

## Camera and sound

- Camera at eye level, 35–50 mm equivalent, locked exposure and white balance.
- Key light 30–45° off axis; practical screen or desk lamp in the background.
- Record the microphone within 15–25 cm, slightly off axis.
- Capture ten seconds of room tone.
- Prefer a clean room over aggressive noise removal.
- Wear a solid neutral color; avoid tight patterns and pure white.

## Screen capture

- Capture at 2560×1440 or higher, 30 fps.
- Browser zoom 110–125% so evidence remains readable after a 1080p export.
- Hide bookmarks, notifications, menu-bar personal data, terminal history and account avatars.
- Use a temporary browser profile and a clean desktop.
- Never show the Razorpay key ID, key secret, webhook secret, local bearer token, CSV path, raw webhook body, signature, contact data or unredacted provider response.
- Move the cursor deliberately. Do not circle continuously.
- Pause for two seconds before and after every important action for editing handles.

## Truth and evidence rules

- The opening is a dramatic reconstruction of the real investigation, not a claimed production incident.
- “Official generated expression” is supportable; “Razorpay generated my entire app” is not established.
- `₹2.01 → ₹2.00`, the SDK collisions and the AES-GCM behavior were dynamically reproduced.
- Wrong JPY/KWD order values were accepted in Test Mode.
- Two hosted legacy Test Mode checkouts reached captured state, but the current Rust quote-to-captured-payment path must not be claimed until separately exercised.
- Provider-side fractional refund acceptance was inconsistent. Never say it always truncates.
- A cross-merchant provider request was not executed. Say “can cross the boundary in a multi-tenant worker,” not “we charged the wrong merchant.”
- Use “23 findings” and “17 direct defects,” not “23 zero-days.”
- No private disclosure status should appear in the pitch.

## Chapter files

Use this edit-bin naming scheme:

```text
01_cold_open/
02_rabbit_hole/
03_missing_layer/
04_razorproof/
05_live_proof/
06_close/
audio/
manim/
screen/
stills/
exports/
```

Name takes as `chapter-shot-take`, for example `04-a_roll-03.mov` or `05-dashboard-replay-02.mov`.

## Quality gate before upload

- Runtime is at most 5:00, including end card.
- First contradiction appears before 0:08.
- Product name appears only after the problem is understood, around 2:02.
- At least one provider-observed Test Mode artifact is legible.
- “Detected,” “prevented,” and “inferred” are visibly distinct.
- Every metric matches the checked-in evidence.
- Repository URL is public and readable for three seconds.
- Captions have been reviewed manually, especially `Razorpay`, `RazorProof`, `paise`, `AES-GCM`, `KWD` and `idempotency`.
- Audio integrated loudness targets approximately −14 to −16 LUFS with peaks below −1 dBTP.
- Export is watched from beginning to end after upload, not only locally.

## Missing inputs before final filming

- Final public GitHub repository URL.
- Final track name exactly as entered in the application.
- Confirmed name/title text for the opening or end card.
- A fresh current-Rust captured-payment receipt, if we decide to make that claim.
- Final decision on whether the face-led sections use English only or a natural English/Malayalam cadence.
