// Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
// SPDX-License-Identifier: MIT
// Licensed under the MIT License. See LICENSE in the repository root.

use serde::{Deserialize, Serialize};
use serde_json::Value;
use thiserror::Error;
use time::OffsetDateTime;
use uuid::Uuid;

use crate::TenantId;

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EvidenceKind {
    RequestAccepted,
    RequestRejected,
    ProviderResponse,
    WebhookAccepted,
    WebhookDuplicate,
    StateTransition,
    ConformanceFinding,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct EvidenceEvent {
    pub id: Uuid,
    pub tenant_id: TenantId,
    pub kind: EvidenceKind,
    pub operation: String,
    pub subject_fingerprint: String,
    pub payload_hash: String,
    pub previous_hash: Option<String>,
    pub chain_hash: String,
    #[serde(with = "time::serde::timestamp")]
    pub occurred_at: OffsetDateTime,
}

impl EvidenceEvent {
    pub fn new(
        tenant_id: TenantId,
        kind: EvidenceKind,
        operation: impl Into<String>,
        subject: &[u8],
        payload: &Value,
        previous_hash: Option<String>,
        occurred_at: OffsetDateTime,
    ) -> Result<Self, EvidenceError> {
        let id = Uuid::now_v7();
        let operation = operation.into();
        let subject_fingerprint = blake3::hash(subject).to_hex()[..16].to_owned();
        let payload_hash = hash_canonical_json(payload)?;
        let link = serde_json::json!({
            "id": id,
            "tenant_id": tenant_id,
            "kind": kind,
            "operation": operation,
            "subject_fingerprint": subject_fingerprint,
            "payload_hash": payload_hash,
            "previous_hash": previous_hash,
            "occurred_at": occurred_at.unix_timestamp_nanos(),
        });
        let chain_hash = hash_canonical_json(&link)?;
        Ok(Self {
            id,
            tenant_id,
            kind,
            operation,
            subject_fingerprint,
            payload_hash,
            previous_hash,
            chain_hash,
            occurred_at,
        })
    }

    pub fn verify_link(&self, expected_previous: Option<&str>) -> Result<(), EvidenceError> {
        if self.previous_hash.as_deref() != expected_previous {
            return Err(EvidenceError::BrokenChain);
        }
        let link = serde_json::json!({
            "id": self.id,
            "tenant_id": self.tenant_id,
            "kind": self.kind,
            "operation": self.operation,
            "subject_fingerprint": self.subject_fingerprint,
            "payload_hash": self.payload_hash,
            "previous_hash": self.previous_hash,
            "occurred_at": self.occurred_at.unix_timestamp_nanos(),
        });
        if hash_canonical_json(&link)? != self.chain_hash {
            return Err(EvidenceError::BrokenChain);
        }
        Ok(())
    }
}

pub fn verify_evidence_chain(events: &[EvidenceEvent]) -> Result<(), EvidenceError> {
    let mut previous = None;
    for event in events {
        event.verify_link(previous)?;
        previous = Some(event.chain_hash.as_str());
    }
    Ok(())
}

pub fn hash_canonical_json(value: &Value) -> Result<String, EvidenceError> {
    let mut output = String::new();
    write_canonical(value, &mut output)?;
    Ok(blake3::hash(output.as_bytes()).to_hex().to_string())
}

fn write_canonical(value: &Value, output: &mut String) -> Result<(), EvidenceError> {
    match value {
        Value::Null => output.push_str("null"),
        Value::Bool(value) => output.push_str(if *value { "true" } else { "false" }),
        Value::Number(value) => {
            // JSON numbers are canonicalized lexically for non-money fields
            // such as ownership percentages. Money validation happens in the
            // operation policy and still requires exact integers.
            output.push_str(&value.to_string());
        }
        Value::String(value) => output.push_str(&serde_json::to_string(value)?),
        Value::Array(values) => {
            output.push('[');
            for (index, value) in values.iter().enumerate() {
                if index > 0 {
                    output.push(',');
                }
                write_canonical(value, output)?;
            }
            output.push(']');
        }
        Value::Object(values) => {
            output.push('{');
            let mut keys = values.keys().collect::<Vec<_>>();
            keys.sort_unstable();
            for (index, key) in keys.into_iter().enumerate() {
                if index > 0 {
                    output.push(',');
                }
                output.push_str(&serde_json::to_string(key)?);
                output.push(':');
                let child = values.get(key).ok_or(EvidenceError::MissingObjectValue)?;
                write_canonical(child, output)?;
            }
            output.push('}');
        }
    }
    Ok(())
}

#[derive(Debug, Error)]
pub enum EvidenceError {
    #[error("object value disappeared during canonicalization")]
    MissingObjectValue,
    #[error("evidence hash chain is broken")]
    BrokenChain,
    #[error(transparent)]
    Json(#[from] serde_json::Error),
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn object_order_does_not_change_hash() -> Result<(), EvidenceError> {
        let left = serde_json::json!({"amount": 201, "currency": "INR"});
        let right = serde_json::json!({"currency": "INR", "amount": 201});
        assert_eq!(hash_canonical_json(&left)?, hash_canonical_json(&right)?);
        assert_eq!(
            hash_canonical_json(&serde_json::json!({"percentage": 87.55}))?,
            hash_canonical_json(&serde_json::json!({"percentage": 87.55}))?
        );
        Ok(())
    }

    #[test]
    fn chain_verifier_detects_tampering() -> Result<(), EvidenceError> {
        let tenant = TenantId::parse("merchant_a").map_err(|_| EvidenceError::BrokenChain)?;
        let first = EvidenceEvent::new(
            tenant.clone(),
            EvidenceKind::RequestAccepted,
            "create_order",
            b"intent_1",
            &serde_json::json!({"amount": 201}),
            None,
            OffsetDateTime::now_utc(),
        )?;
        let mut second = EvidenceEvent::new(
            tenant,
            EvidenceKind::ProviderResponse,
            "create_order",
            b"intent_1",
            &serde_json::json!({"status": 200}),
            Some(first.chain_hash.clone()),
            OffsetDateTime::now_utc(),
        )?;
        assert!(verify_evidence_chain(&[first.clone(), second.clone()]).is_ok());
        second.operation = "create_refund".to_owned();
        assert!(verify_evidence_chain(&[first, second]).is_err());
        Ok(())
    }
}
