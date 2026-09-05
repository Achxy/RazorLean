// Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
// SPDX-License-Identifier: MIT
// Licensed under the MIT License. See LICENSE in the repository root.

use serde::{Deserialize, Serialize};
use thiserror::Error;
use time::OffsetDateTime;

use crate::{Currency, MinorAmount, Money, MoneyError, QuoteId, TenantId, hash_canonical_json};

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct QuoteLine {
    pub sku: String,
    pub unit_amount: MinorAmount,
    pub quantity: u32,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
#[serde(tag = "state", rename_all = "snake_case")]
pub enum QuoteState {
    Issued,
    OrderBound {
        provider_order_id: String,
    },
    PaymentVerified {
        provider_order_id: String,
        provider_payment_id: String,
    },
    Fulfilled {
        provider_payment_id: String,
        fulfillment_reference: String,
    },
    Cancelled,
    Expired,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct Quote {
    pub id: QuoteId,
    pub tenant_id: TenantId,
    pub money: Money,
    pub cart_hash: String,
    pub lines: Vec<QuoteLine>,
    #[serde(with = "time::serde::timestamp")]
    pub expires_at: OffsetDateTime,
    pub state: QuoteState,
    pub version: u64,
}

impl Quote {
    pub fn issue(
        tenant_id: TenantId,
        currency: Currency,
        lines: Vec<QuoteLine>,
        expires_at: OffsetDateTime,
    ) -> Result<Self, QuoteError> {
        if lines.is_empty() || lines.len() > 128 {
            return Err(QuoteError::InvalidLineCount);
        }
        if expires_at <= OffsetDateTime::now_utc() {
            return Err(QuoteError::AlreadyExpired);
        }
        let mut total: Option<MinorAmount> = None;
        for line in &lines {
            validate_sku(&line.sku)?;
            if line.quantity == 0 || line.quantity > 100_000 {
                return Err(QuoteError::InvalidQuantity);
            }
            let line_total = line.unit_amount.checked_mul(line.quantity)?;
            total = Some(match total {
                Some(value) => value.checked_add(line_total)?,
                None => line_total,
            });
        }
        let amount = total.ok_or(QuoteError::InvalidLineCount)?;
        let money = Money::from_minor(amount.get(), currency)?;
        let cart_hash = hash_canonical_json(&serde_json::to_value(&lines)?)?;
        Ok(Self {
            id: QuoteId::new(),
            tenant_id,
            money,
            cart_hash,
            lines,
            expires_at,
            state: QuoteState::Issued,
            version: 1,
        })
    }

    pub fn bind_order(
        &mut self,
        provider_order_id: impl Into<String>,
        now: OffsetDateTime,
    ) -> Result<(), QuoteError> {
        self.ensure_live(now)?;
        if self.state != QuoteState::Issued {
            return Err(QuoteError::InvalidTransition);
        }
        let provider_order_id = provider_order_id.into();
        validate_provider_id(&provider_order_id, "order_")?;
        self.state = QuoteState::OrderBound { provider_order_id };
        self.version += 1;
        Ok(())
    }

    pub fn verify_payment(
        &mut self,
        provider_order_id: &str,
        provider_payment_id: impl Into<String>,
        now: OffsetDateTime,
    ) -> Result<(), QuoteError> {
        self.ensure_live(now)?;
        let QuoteState::OrderBound {
            provider_order_id: expected,
        } = &self.state
        else {
            return Err(QuoteError::InvalidTransition);
        };
        if expected != provider_order_id {
            return Err(QuoteError::OrderMismatch);
        }
        let provider_payment_id = provider_payment_id.into();
        validate_provider_id(&provider_payment_id, "pay_")?;
        self.state = QuoteState::PaymentVerified {
            provider_order_id: expected.clone(),
            provider_payment_id,
        };
        self.version += 1;
        Ok(())
    }

    pub fn fulfill(&mut self, reference: impl Into<String>) -> Result<(), QuoteError> {
        let QuoteState::PaymentVerified {
            provider_payment_id,
            ..
        } = &self.state
        else {
            return Err(QuoteError::InvalidTransition);
        };
        let reference = reference.into();
        if reference.is_empty() || reference.len() > 128 {
            return Err(QuoteError::InvalidFulfillmentReference);
        }
        self.state = QuoteState::Fulfilled {
            provider_payment_id: provider_payment_id.clone(),
            fulfillment_reference: reference,
        };
        self.version += 1;
        Ok(())
    }

    fn ensure_live(&mut self, now: OffsetDateTime) -> Result<(), QuoteError> {
        if now >= self.expires_at {
            self.state = QuoteState::Expired;
            self.version += 1;
            return Err(QuoteError::Expired);
        }
        Ok(())
    }
}

fn validate_sku(value: &str) -> Result<(), QuoteError> {
    if value.is_empty()
        || value.len() > 96
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.' | b':'))
    {
        return Err(QuoteError::InvalidSku);
    }
    Ok(())
}

fn validate_provider_id(value: &str, prefix: &str) -> Result<(), QuoteError> {
    if !value.starts_with(prefix)
        || value.len() > 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_')
    {
        return Err(QuoteError::MalformedProviderId);
    }
    Ok(())
}

#[derive(Debug, Error)]
pub enum QuoteError {
    #[error("a quote must contain between 1 and 128 lines")]
    InvalidLineCount,
    #[error("invalid SKU")]
    InvalidSku,
    #[error("quantity must be between 1 and 100000")]
    InvalidQuantity,
    #[error("quote expiry must be in the future")]
    AlreadyExpired,
    #[error("quote expired")]
    Expired,
    #[error("invalid quote state transition")]
    InvalidTransition,
    #[error("provider order does not match the server-bound order")]
    OrderMismatch,
    #[error("provider identifier is malformed")]
    MalformedProviderId,
    #[error("fulfillment reference is invalid")]
    InvalidFulfillmentReference,
    #[error(transparent)]
    Money(#[from] MoneyError),
    #[error(transparent)]
    Json(#[from] serde_json::Error),
    #[error(transparent)]
    Evidence(#[from] crate::evidence::EvidenceError),
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn quote_is_server_valued_and_single_transitioned() -> Result<(), QuoteError> {
        let now = OffsetDateTime::now_utc();
        let mut quote = Quote::issue(
            TenantId::parse("merchant_a").map_err(|_| QuoteError::InvalidSku)?,
            Currency::parse("INR")?,
            vec![QuoteLine {
                sku: "sku_pro".to_owned(),
                unit_amount: MinorAmount::new(201)?,
                quantity: 2,
            }],
            now + time::Duration::minutes(10),
        )?;
        assert_eq!(quote.money.amount.get(), 402);
        quote.bind_order("order_1234567890", now)?;
        assert!(quote.bind_order("order_other", now).is_err());
        assert!(
            quote
                .verify_payment("order_wrong", "pay_1234567890", now)
                .is_err()
        );
        quote.verify_payment("order_1234567890", "pay_1234567890", now)?;
        quote.fulfill("fulfillment_1")?;
        assert!(quote.fulfill("fulfillment_2").is_err());
        Ok(())
    }
}
