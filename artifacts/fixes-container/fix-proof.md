# RazorProof Red to Green Fix Proof

All proposed fixes passed: **True**

## RP-MCP-GENERATOR-MONEY-UNDERCHARGE

- Fixed: `True`
- Scope: RazorProof exact-money boundary
- Before: `{"input": 2.01, "minor_units": 200}`
- After: `{"binary_float_rejected": true, "input": "2.01", "minor_units": 201}`

## RP-PYTHON-WEBHOOK-BYTES

- Fixed: `True`
- Scope: disposable clean clone
- Before: `{"accepted": false, "error": "TypeError: encoding without a string argument"}`
- After: `{"accepted": true, "error": ""}`

## RP-RUBY-PAYLINK-ORDER

- Fixed: `True`
- Scope: disposable clean clone
- Before: `{"accepted": false, "caller_signature_preserved": false, "error": "SecurityError: Signature verification failed"}`
- After: `{"accepted": true, "caller_signature_preserved": true, "error": ""}`

## RP-MCP-REFUND-TRUNCATION

- Fixed: `True`
- Scope: disposable clean clone; official handler and SDK HTTP path; proves fractional rejection and valid-integer acceptance
- Before: `{"exit": 1, "tail": "=== RUN   TestRazorProofFractionalRefundMustFailClosed\nlogs are stored in: /tmp/go-build3652567974/b001/logs\n    razorproof_fractional_test.go:33: fractional money crossed the MCP boundary: requested=100.75 sent=100\n--- FAIL: TestRazorProofFractionalRefundMustFailClosed (0.01s)\nFAIL\nFAIL\tgithub.com/razorpay/razorpay-mcp-server/pkg/razorpay\t0.011s\nFAIL\ngo: downloading github.com/go-test/deep v1.1.1\ngo: downloading github.com/razorpay/razorpay-go v1.4.0\ngo: downloading github.com/stretchr/testify v1.10.0\ngo: downloading github.com/mark3labs/mcp-go v0.43.2\ngo: downloading github.com/gorilla/mux v1.8.1\ngo: downloading github.com/davecgh/go-spew v1.1.1\ngo: downloading github.com/pmezard/go-difflib v1.0.0\ngo: downloading gopkg.in/yaml.v3 v3.0.1\ngo: downloading github.com/yosida95/uritemplate/v3 v3.0.2\ngo: downloading github.com/invopop/jsonschema v0.13.0\ngo: downloading github.com/spf13/cast v1.7.1\ngo: downloading github.com/google/uuid v1.6.0\ngo: downloading github.com/wk8/go-ordered-map/v2 v2.1.8\ngo: downloading github.com/mailru/easyjson v0.7.7\ngo: downloading github.com/bahlo/generic-list-go v0.2.0\ngo: downloading github.com/buger/jsonparser v1.1.1\n"}`
- After: `{"exit": 0, "tail": "=== RUN   TestRazorProofFractionalRefundMustFailClosed\nlogs are stored in: /tmp/go-build1578571075/b001/logs\n--- PASS: TestRazorProofFractionalRefundMustFailClosed (0.00s)\nPASS\nok  \tgithub.com/razorpay/razorpay-mcp-server/pkg/razorpay\t0.007s\ngo: downloading github.com/razorpay/razorpay-go v1.4.0\ngo: downloading github.com/go-test/deep v1.1.1\ngo: downloading github.com/stretchr/testify v1.10.0\ngo: downloading github.com/mark3labs/mcp-go v0.43.2\ngo: downloading github.com/gorilla/mux v1.8.1\ngo: downloading gopkg.in/yaml.v3 v3.0.1\ngo: downloading github.com/davecgh/go-spew v1.1.1\ngo: downloading github.com/pmezard/go-difflib v1.0.0\ngo: downloading github.com/yosida95/uritemplate/v3 v3.0.2\ngo: downloading github.com/invopop/jsonschema v0.13.0\ngo: downloading github.com/google/uuid v1.6.0\ngo: downloading github.com/spf13/cast v1.7.1\ngo: downloading github.com/wk8/go-ordered-map/v2 v2.1.8\ngo: downloading github.com/mailru/easyjson v0.7.7\ngo: downloading github.com/buger/jsonparser v1.1.1\ngo: downloading github.com/bahlo/generic-list-go v0.2.0\n"}`

## RP-DOTNET-GCM-NONCE-REUSE + RP-DOTNET-WEBHOOK-ASCII

- Fixed: `True`
- Scope: disposable clean clone; official SDK project
- Before: `{"gcm_same": true, "source": "successful container scan", "unicode_accepted": false}`
- After: `{"exit": 0, "first_prefix": "8b880b41d9a490c9b145c607", "gcm_same": false, "unicode_accepted": true, "unicode_error": ""}`
