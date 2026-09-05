// Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
// SPDX-License-Identifier: MIT
// Licensed under the MIT License. See LICENSE in the repository root.

use hmac::{Hmac, Mac};
use sha2::Sha256;
use subtle::ConstantTimeEq;
use thiserror::Error;

type HmacSha256 = Hmac<Sha256>;

pub fn verify_webhook_signature(
    raw_body: &[u8],
    received_hex: &str,
    secret: &[u8],
) -> Result<(), SignatureError> {
    verify_hmac(raw_body, received_hex, secret)
}

pub fn verify_checkout_signature(
    server_order_id: &str,
    payment_id: &str,
    received_hex: &str,
    secret: &[u8],
) -> Result<(), SignatureError> {
    validate_provider_id(server_order_id, "order_")?;
    validate_provider_id(payment_id, "pay_")?;
    let payload = format!("{server_order_id}|{payment_id}");
    verify_hmac(payload.as_bytes(), received_hex, secret)
}

fn verify_hmac(payload: &[u8], received_hex: &str, secret: &[u8]) -> Result<(), SignatureError> {
    if secret.len() < 16 {
        return Err(SignatureError::WeakSecret);
    }
    if received_hex.len() != 64 || !received_hex.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(SignatureError::MalformedSignature);
    }
    let received = hex::decode(received_hex).map_err(|_| SignatureError::MalformedSignature)?;
    let mut mac = HmacSha256::new_from_slice(secret).map_err(|_| SignatureError::WeakSecret)?;
    mac.update(payload);
    let expected = mac.finalize().into_bytes();
    if expected.as_slice().ct_eq(received.as_slice()).into() {
        Ok(())
    } else {
        Err(SignatureError::Mismatch)
    }
}

fn validate_provider_id(value: &str, prefix: &str) -> Result<(), SignatureError> {
    if !value.starts_with(prefix)
        || value.len() > 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_')
    {
        return Err(SignatureError::MalformedIdentifier);
    }
    Ok(())
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum SignatureError {
    #[error("signature must be exactly 64 hexadecimal characters")]
    MalformedSignature,
    #[error("provider identifier is malformed")]
    MalformedIdentifier,
    #[error("secret is too short")]
    WeakSecret,
    #[error("signature mismatch")]
    Mismatch,
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sign(payload: &[u8], secret: &[u8]) -> Result<String, SignatureError> {
        let mut mac = HmacSha256::new_from_slice(secret).map_err(|_| SignatureError::WeakSecret)?;
        mac.update(payload);
        Ok(hex::encode(mac.finalize().into_bytes()))
    }

    #[test]
    fn verifies_literal_utf8_bytes_and_rejects_mutation() -> Result<(), SignatureError> {
        let secret = b"test_webhook_secret_32_bytes_long";
        let body = "{\"note\":\"₹ മലയാളം\"}".as_bytes();
        let signature = sign(body, secret)?;
        assert!(verify_webhook_signature(body, &signature, secret).is_ok());
        assert!(verify_webhook_signature(b"{}", &signature, secret).is_err());
        Ok(())
    }

    #[test]
    fn rejects_bad_length_without_panicking() {
        let result = verify_webhook_signature(b"{}", "f", b"test_webhook_secret_32_bytes_long");
        assert_eq!(result, Err(SignatureError::MalformedSignature));
    }
}
