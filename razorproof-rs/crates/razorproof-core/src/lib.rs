#![doc = "Economic and cryptographic primitives for RazorProof."]
// Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
// SPDX-License-Identifier: MIT
// Licensed under the MIT License. See LICENSE in the repository root.

mod crypto;
mod evidence;
mod identity;
mod money;
mod quote;

pub use crypto::{SignatureError, verify_checkout_signature, verify_webhook_signature};
pub use evidence::{
    EvidenceError, EvidenceEvent, EvidenceKind, hash_canonical_json, verify_evidence_chain,
};
pub use identity::{IdentityError, IntentId, QuoteId, TenantId};
pub use money::{Currency, CurrencyRule, MinorAmount, Money, MoneyError};
pub use quote::{Quote, QuoteError, QuoteLine, QuoteState};
