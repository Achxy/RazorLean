## Summary

The Java SDK's document multipart serializer has two independent wire-format defects in one request:

1. Runtime JPG/JPEG/PNG/JFIF paths are compared with `==`, so a normal `proof.png` path is classified as `image/pdf`. PDF also falls through to the non-standard `image/pdf` rather than documented `application/pdf`.
2. The serializer adds `file` once as a binary part, then iterates the complete request object and adds the same `file` key again as a text pathname.

Affected commit: `ad9ab7b6e6f045b782dfd7608da04de9f930ad97`

## Reproduction

I executed the pinned official SDK serializer through reflection and wrote the resulting `RequestBody` to an Okio buffer:

```json
{
  "png_media_type": "image/pdf",
  "file_parts": 2
}
```

Input shape:

```json
{
  "file": "/tmp/proof.png",
  "purpose": "dispute_evidence"
}
```

Relevant source is `src/main/java/com/razorpay/ApiUtils.java`:

- `getMediaType` compares the substring extension using `==` and `|`.
- `fileRequestBody` adds the binary `file` part.
- Its following loop adds every request key, including `file`, again as a text part.

The Document API documents a singular `file` field and MIME values `image/jpg`, `image/jpeg`, `image/png`, and `application/pdf`.

## Expected

- One binary multipart part named `file`.
- Correct documented MIME type for the selected file.
- Unknown extensions rejected rather than classified as PDF.

## Suggested fix

- Map lower-cased extensions with `.equals`/`.equalsIgnoreCase` to their exact MIME types.
- Exclude `file` from the ordinary form-field loop.
- Add a multipart wire snapshot test asserting both MIME and field cardinality.

No credentials or provider-side mutation are required to reproduce this SDK serialization defect.
