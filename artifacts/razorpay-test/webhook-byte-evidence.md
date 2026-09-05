# Razorpay Test Mode: Literal UTF-8 Webhook Evidence

- Captured signed deliveries: `22`
- Literal non-ASCII deliveries: `16`
- All capture signatures valid: `True`
- Exact UTF-8 bytes verify: `True`
- .NET ASCII substitution fails verification: `True`

## Event coverage

| Event | Deliveries |
|---|---:|
| `payment.authorized` | `2` |
| `payment.captured` | `2` |
| `payment.failed` | `2` |
| `payment_link.paid` | `2` |
| `refund.created` | `7` |
| `refund.processed` | `7` |

## Literal-byte observations

| Event | Bytes | Raw SHA-256 | Exact UTF-8 | .NET ASCII | Non-ASCII paths |
|---|---:|---|---|---|---|
| `payment_link.paid` | `2218` | `098dee525dc1926958595bc6ced0ca034b5f680767ca8e5d057e528ed7a4e24c` | `True` | `False` | `$.payload.order.entity.notes.unicode_probe`, `$.payload.payment.entity.notes.unicode_probe`, `$.payload.payment_link.entity.description`, `$.payload.payment_link.entity.notes.unicode_probe` |
| `refund.created` | `1790` | `8e10e4571be26f638e5dc08cb758da8a105bd0c2c85d850768f211bacc518e7a` | `True` | `False` | `$.payload.payment.entity.notes.unicode_probe` |
| `refund.processed` | `1792` | `d305bcaba499f9bc6b040773483da502a2958627766e100e6fd85777c7580df7` | `True` | `False` | `$.payload.payment.entity.notes.unicode_probe` |
| `payment_link.paid` | `2210` | `7261181ef8d2ed732d6b93a85eb98016f36fdbcecbc3d358e06a2bcc09cd90b1` | `True` | `False` | `$.payload.order.entity.notes.unicode_probe`, `$.payload.payment.entity.notes.unicode_probe`, `$.payload.payment_link.entity.description`, `$.payload.payment_link.entity.notes.unicode_probe` |
| `refund.created` | `1781` | `d40a6dd52e7bd5603e1e705268c8fd156f3abba3a314f480aec6856b4e6fbe1e` | `True` | `False` | `$.payload.payment.entity.notes.unicode_probe` |
| `refund.processed` | `1783` | `1c8dac5c70e3fcd3861ff8d8ae9a58dfbf46648c200d7b00296826fd9208e9ac` | `True` | `False` | `$.payload.payment.entity.notes.unicode_probe` |
| `refund.created` | `1810` | `eb1977c83e28521612abdcdbb8e898493e0aa5fd77014f70e6eb12ed1d4be087` | `True` | `False` | `$.payload.payment.entity.notes.unicode_probe` |
| `refund.processed` | `1788` | `85b4e961b594a583478cdea64297b7706625f37369d0e55df13cb2c48f7bd124` | `True` | `False` | `$.payload.payment.entity.notes.unicode_probe` |
| `refund.processed` | `1812` | `0aa2a226ed8150ae00a361a0e0ac598ba97ea7d12c5ff6943f2f39dc987ed713` | `True` | `False` | `$.payload.payment.entity.notes.unicode_probe` |
| `refund.created` | `1782` | `e2d165bb3bf92fa2eec1c6156643a456e0dd6aa69e6187fc5044cf84592118c2` | `True` | `False` | `$.payload.payment.entity.notes.unicode_probe` |
| `refund.created` | `1782` | `c61ab5e64791a05f796cb7979c52fb117797c043c79cf5d8fcb996875abb0bba` | `True` | `False` | `$.payload.payment.entity.notes.unicode_probe` |
| `refund.processed` | `1784` | `be0120cfaa3e5de36b28982ee5c844969297e1a8b267e426b61f96e3eb5075a5` | `True` | `False` | `$.payload.payment.entity.notes.unicode_probe` |
| `refund.processed` | `1784` | `b0dc9f993603c3fb693997aa67e461aa076f611074d5549911d8093ebc13e088` | `True` | `False` | `$.payload.payment.entity.notes.unicode_probe` |
| `refund.created` | `1786` | `fd307ec7f1785cbec049186bbf8ec116728db0506acecb256cad10a2b6556695` | `True` | `False` | `$.payload.payment.entity.notes.unicode_probe` |
| `refund.created` | `1785` | `9302dde6c4c233e64940de839dcdbdd5128ac3d7082ff0e71f5544f10b50aad1` | `True` | `False` | `$.payload.payment.entity.notes.unicode_probe` |
| `refund.processed` | `1787` | `8d9f02d6f7eddf01f579ee3621fb23685bbb048c35070c3b56fee9317fa67302` | `True` | `False` | `$.payload.payment.entity.notes.unicode_probe` |

Razorpay signed the exact raw UTF-8 bytes delivered to the Test Mode endpoint. Re-encoding the same payload text with ASCII replacement changes those bytes and produces a different HMAC. This closes the former reachability caveat for the current .NET SDK's shared ASCII encoder: ordinary provider-generated payment-link and refund webhooks can contain literal non-ASCII bytes.

This artifact intentionally omits raw payloads, signatures, headers, entity IDs, contact data, and the signing secret. SHA-256 values identify the private captures without disclosing them.
