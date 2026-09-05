# Mobile Dependency Registry Evidence

- Registry: `https://registry.npmjs.org`
- Captured: `2026-09-03T10:51:15.442083+00:00`

| Generator path | Package | Exists | Version | Description | Files | Repository |
|---|---|---|---|---|---:|---|
| `generated_cordova_and_ionic` | `com.nicholaswilliams.nicepay.razorpay` | `False` | `` |  | `` | `` |
| `generated_capacitor` | `cordova-plugin-razorpay` | `True` | `0.3.5` | Empty package. | `2` | `` |
| `razorpay_official_control` | `com.razorpay.cordova` | `True` | `1.4.15` | Cordova/Phonegap bindings for Razorpay's Mobile SDKs | `22` | `git+https://github.com/razorpay/razorpay-cordova.git` |

The official MCP generator emits the first package for Cordova and Ionic and the second for Capacitor. The first returns npm 404. The second is a 179-byte, two-file package whose own description and README say `Empty package.` It is not linked to Razorpay's repository. The official control package is `com.razorpay.cordova`, lists Razorpay's npm maintainer identity, and links to the Razorpay GitHub repository.

This proves a present dependency identity defect. Arbitrary-code execution is a supply-chain risk, not a claim that the current empty package is malicious.
