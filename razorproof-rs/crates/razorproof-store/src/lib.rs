#![doc = "Durable SQLite state and hash-chained evidence for RazorProof."]
// Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
// SPDX-License-Identifier: MIT
// Licensed under the MIT License. See LICENSE in the repository root.

use std::str::FromStr;

use razorproof_core::{EvidenceEvent, EvidenceKind, IntentId, Quote, QuoteId, TenantId};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sqlx::{
    Row, SqlitePool,
    sqlite::{SqliteConnectOptions, SqlitePoolOptions},
};
use thiserror::Error;
use time::OffsetDateTime;

#[derive(Clone)]
pub struct Store {
    pool: SqlitePool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum EffectClaim {
    New,
    InFlight,
    Replay { response: Value },
    Conflict,
    PriorFailure,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct WebhookReceipt {
    pub duplicate: bool,
    pub event_id_fingerprint: String,
    pub body_hash: String,
}

impl Store {
    pub async fn connect(database_url: &str) -> Result<Self, StoreError> {
        let options = SqliteConnectOptions::from_str(database_url)?
            .create_if_missing(true)
            .foreign_keys(true)
            .busy_timeout(std::time::Duration::from_secs(5));
        // An in-memory SQLite database is scoped to one connection. Keeping the
        // pool at one connection prevents tests and ephemeral demos from seeing
        // different databases as the pool schedules work.
        let max_connections = if database_url == "sqlite::memory:" {
            1
        } else {
            8
        };
        let pool = SqlitePoolOptions::new()
            .max_connections(max_connections)
            .connect_with(options)
            .await?;
        let store = Self { pool };
        store.migrate().await?;
        Ok(store)
    }

    pub async fn in_memory() -> Result<Self, StoreError> {
        Self::connect("sqlite::memory:").await
    }

    async fn migrate(&self) -> Result<(), StoreError> {
        let statements = [
            "PRAGMA journal_mode = WAL",
            "PRAGMA synchronous = FULL",
            "CREATE TABLE IF NOT EXISTS quotes (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, version INTEGER NOT NULL, quote_json TEXT NOT NULL, updated_at INTEGER NOT NULL)",
            "CREATE INDEX IF NOT EXISTS quotes_tenant ON quotes(tenant_id, updated_at)",
            "CREATE TABLE IF NOT EXISTS effects (tenant_id TEXT NOT NULL, intent_id TEXT NOT NULL, operation TEXT NOT NULL, body_hash TEXT NOT NULL, status TEXT NOT NULL, response_json TEXT, error_code TEXT, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL, PRIMARY KEY(tenant_id, intent_id))",
            "CREATE INDEX IF NOT EXISTS effects_operation ON effects(tenant_id, operation, created_at)",
            "CREATE TABLE IF NOT EXISTS webhook_events (tenant_id TEXT NOT NULL, event_id_hash TEXT NOT NULL, event_type TEXT NOT NULL, body_hash TEXT NOT NULL, received_at INTEGER NOT NULL, PRIMARY KEY(tenant_id, event_id_hash))",
            "CREATE TABLE IF NOT EXISTS evidence (sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL UNIQUE, tenant_id TEXT NOT NULL, kind TEXT NOT NULL, operation TEXT NOT NULL, subject_fingerprint TEXT NOT NULL, payload_hash TEXT NOT NULL, previous_hash TEXT, chain_hash TEXT NOT NULL, occurred_at INTEGER NOT NULL)",
            "CREATE INDEX IF NOT EXISTS evidence_tenant ON evidence(tenant_id, sequence)",
            "CREATE UNIQUE INDEX IF NOT EXISTS evidence_single_successor ON evidence(tenant_id, previous_hash) WHERE previous_hash IS NOT NULL",
        ];
        for statement in statements {
            sqlx::query(statement).execute(&self.pool).await?;
        }
        Ok(())
    }

    pub async fn health(&self) -> Result<(), StoreError> {
        sqlx::query("SELECT 1").execute(&self.pool).await?;
        Ok(())
    }

    pub async fn insert_quote(&self, quote: &Quote) -> Result<(), StoreError> {
        let quote_json = serde_json::to_string(quote)?;
        sqlx::query("INSERT INTO quotes(id, tenant_id, version, quote_json, updated_at) VALUES(?, ?, ?, ?, ?)")
            .bind(quote.id.as_str())
            .bind(quote.tenant_id.as_str())
            .bind(i64::try_from(quote.version).map_err(|_| StoreError::VersionOverflow)?)
            .bind(quote_json)
            .bind(OffsetDateTime::now_utc().unix_timestamp())
            .execute(&self.pool)
            .await?;
        Ok(())
    }

    pub async fn get_quote(
        &self,
        tenant_id: &TenantId,
        quote_id: &QuoteId,
    ) -> Result<Option<Quote>, StoreError> {
        let row = sqlx::query("SELECT quote_json FROM quotes WHERE id = ? AND tenant_id = ?")
            .bind(quote_id.as_str())
            .bind(tenant_id.as_str())
            .fetch_optional(&self.pool)
            .await?;
        row.map(|row| serde_json::from_str(row.get::<&str, _>("quote_json")))
            .transpose()
            .map_err(StoreError::from)
    }

    pub async fn update_quote(
        &self,
        quote: &Quote,
        expected_version: u64,
    ) -> Result<(), StoreError> {
        let quote_json = serde_json::to_string(quote)?;
        let result = sqlx::query("UPDATE quotes SET version = ?, quote_json = ?, updated_at = ? WHERE id = ? AND tenant_id = ? AND version = ?")
            .bind(i64::try_from(quote.version).map_err(|_| StoreError::VersionOverflow)?)
            .bind(quote_json)
            .bind(OffsetDateTime::now_utc().unix_timestamp())
            .bind(quote.id.as_str())
            .bind(quote.tenant_id.as_str())
            .bind(i64::try_from(expected_version).map_err(|_| StoreError::VersionOverflow)?)
            .execute(&self.pool)
            .await?;
        if result.rows_affected() != 1 {
            return Err(StoreError::OptimisticConflict);
        }
        Ok(())
    }

    pub async fn claim_effect(
        &self,
        tenant_id: &TenantId,
        intent_id: &IntentId,
        operation: &str,
        body_hash: &str,
    ) -> Result<EffectClaim, StoreError> {
        let mut transaction = self.pool.begin().await?;
        let existing = sqlx::query("SELECT operation, body_hash, status, response_json FROM effects WHERE tenant_id = ? AND intent_id = ?")
            .bind(tenant_id.as_str())
            .bind(intent_id.as_str())
            .fetch_optional(&mut *transaction)
            .await?;
        if let Some(row) = existing {
            let same = row.get::<&str, _>("operation") == operation
                && row.get::<&str, _>("body_hash") == body_hash;
            if !same {
                transaction.rollback().await?;
                return Ok(EffectClaim::Conflict);
            }
            let claim = match row.get::<&str, _>("status") {
                "pending" => EffectClaim::InFlight,
                "completed" => {
                    let response = row
                        .try_get::<Option<&str>, _>("response_json")?
                        .ok_or(StoreError::CorruptCompletedEffect)?;
                    EffectClaim::Replay {
                        response: serde_json::from_str(response)?,
                    }
                }
                "failed" => EffectClaim::PriorFailure,
                state => return Err(StoreError::UnknownEffectState(state.to_owned())),
            };
            transaction.rollback().await?;
            return Ok(claim);
        }
        let now = OffsetDateTime::now_utc().unix_timestamp();
        sqlx::query("INSERT INTO effects(tenant_id, intent_id, operation, body_hash, status, created_at, updated_at) VALUES(?, ?, ?, ?, 'pending', ?, ?)")
            .bind(tenant_id.as_str())
            .bind(intent_id.as_str())
            .bind(operation)
            .bind(body_hash)
            .bind(now)
            .bind(now)
            .execute(&mut *transaction)
            .await?;
        transaction.commit().await?;
        Ok(EffectClaim::New)
    }

    pub async fn complete_effect(
        &self,
        tenant_id: &TenantId,
        intent_id: &IntentId,
        response: &Value,
    ) -> Result<(), StoreError> {
        let result = sqlx::query("UPDATE effects SET status = 'completed', response_json = ?, updated_at = ? WHERE tenant_id = ? AND intent_id = ? AND status = 'pending'")
            .bind(serde_json::to_string(response)?)
            .bind(OffsetDateTime::now_utc().unix_timestamp())
            .bind(tenant_id.as_str())
            .bind(intent_id.as_str())
            .execute(&self.pool)
            .await?;
        if result.rows_affected() != 1 {
            return Err(StoreError::InvalidEffectTransition);
        }
        Ok(())
    }

    pub async fn fail_effect(
        &self,
        tenant_id: &TenantId,
        intent_id: &IntentId,
        error_code: &str,
    ) -> Result<(), StoreError> {
        let result = sqlx::query("UPDATE effects SET status = 'failed', error_code = ?, updated_at = ? WHERE tenant_id = ? AND intent_id = ? AND status = 'pending'")
            .bind(error_code)
            .bind(OffsetDateTime::now_utc().unix_timestamp())
            .bind(tenant_id.as_str())
            .bind(intent_id.as_str())
            .execute(&self.pool)
            .await?;
        if result.rows_affected() != 1 {
            return Err(StoreError::InvalidEffectTransition);
        }
        Ok(())
    }

    pub async fn record_webhook(
        &self,
        tenant_id: &TenantId,
        event_id: &str,
        event_type: &str,
        raw_body: &[u8],
    ) -> Result<WebhookReceipt, StoreError> {
        if event_id.is_empty()
            || event_id.len() > 256
            || event_type.is_empty()
            || event_type.len() > 128
        {
            return Err(StoreError::InvalidWebhookMetadata);
        }
        let event_id_fingerprint = blake3::hash(event_id.as_bytes()).to_hex().to_string();
        let body_hash = blake3::hash(raw_body).to_hex().to_string();
        let result = sqlx::query("INSERT OR IGNORE INTO webhook_events(tenant_id, event_id_hash, event_type, body_hash, received_at) VALUES(?, ?, ?, ?, ?)")
            .bind(tenant_id.as_str())
            .bind(&event_id_fingerprint)
            .bind(event_type)
            .bind(&body_hash)
            .bind(OffsetDateTime::now_utc().unix_timestamp())
            .execute(&self.pool)
            .await?;
        Ok(WebhookReceipt {
            duplicate: result.rows_affected() == 0,
            event_id_fingerprint: event_id_fingerprint[..16].to_owned(),
            body_hash,
        })
    }

    pub async fn append_evidence(
        &self,
        tenant_id: TenantId,
        kind: EvidenceKind,
        operation: impl Into<String>,
        subject: &[u8],
        payload: &Value,
    ) -> Result<EvidenceEvent, StoreError> {
        let mut transaction = self.pool.begin().await?;
        let previous_hash = sqlx::query(
            "SELECT chain_hash FROM evidence WHERE tenant_id = ? ORDER BY sequence DESC LIMIT 1",
        )
        .bind(tenant_id.as_str())
        .fetch_optional(&mut *transaction)
        .await?
        .map(|row| row.get::<String, _>("chain_hash"));
        let event = EvidenceEvent::new(
            tenant_id,
            kind,
            operation,
            subject,
            payload,
            previous_hash,
            OffsetDateTime::now_utc(),
        )?;
        let occurred_at = i64::try_from(event.occurred_at.unix_timestamp_nanos())
            .map_err(|_| StoreError::TimeOverflow)?;
        sqlx::query("INSERT INTO evidence(id, tenant_id, kind, operation, subject_fingerprint, payload_hash, previous_hash, chain_hash, occurred_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)")
            .bind(event.id.to_string())
            .bind(event.tenant_id.as_str())
            .bind(serde_json::to_string(&event.kind)?)
            .bind(&event.operation)
            .bind(&event.subject_fingerprint)
            .bind(&event.payload_hash)
            .bind(&event.previous_hash)
            .bind(&event.chain_hash)
            .bind(occurred_at)
            .execute(&mut *transaction)
            .await?;
        transaction.commit().await?;
        Ok(event)
    }

    pub async fn list_evidence(
        &self,
        tenant_id: &TenantId,
        limit: u32,
    ) -> Result<Vec<EvidenceEvent>, StoreError> {
        let limit = i64::from(limit.clamp(1, 500));
        let rows = sqlx::query("SELECT id, tenant_id, kind, operation, subject_fingerprint, payload_hash, previous_hash, chain_hash, occurred_at FROM evidence WHERE tenant_id = ? ORDER BY sequence DESC LIMIT ?")
            .bind(tenant_id.as_str())
            .bind(limit)
            .fetch_all(&self.pool)
            .await?;
        rows.into_iter()
            .map(|row| {
                let id = uuid::Uuid::parse_str(row.get::<&str, _>("id"))?;
                let tenant_id = TenantId::parse(row.get::<&str, _>("tenant_id"))?;
                let kind = serde_json::from_str(row.get::<&str, _>("kind"))?;
                let occurred_at = OffsetDateTime::from_unix_timestamp_nanos(i128::from(
                    row.get::<i64, _>("occurred_at"),
                ))?;
                Ok(EvidenceEvent {
                    id,
                    tenant_id,
                    kind,
                    operation: row.get("operation"),
                    subject_fingerprint: row.get("subject_fingerprint"),
                    payload_hash: row.get("payload_hash"),
                    previous_hash: row.get("previous_hash"),
                    chain_hash: row.get("chain_hash"),
                    occurred_at,
                })
            })
            .collect()
    }
}

#[derive(Debug, Error)]
pub enum StoreError {
    #[error(transparent)]
    Sqlx(#[from] sqlx::Error),
    #[error(transparent)]
    Json(#[from] serde_json::Error),
    #[error(transparent)]
    Evidence(#[from] razorproof_core::EvidenceError),
    #[error(transparent)]
    Identity(#[from] razorproof_core::IdentityError),
    #[error(transparent)]
    Uuid(#[from] uuid::Error),
    #[error(transparent)]
    Time(#[from] time::error::ComponentRange),
    #[error("timestamp exceeds SQLite integer range")]
    TimeOverflow,
    #[error("quote version exceeds SQLite integer range")]
    VersionOverflow,
    #[error("quote was concurrently modified")]
    OptimisticConflict,
    #[error("completed effect has no stored response")]
    CorruptCompletedEffect,
    #[error("unknown effect state: {0}")]
    UnknownEffectState(String),
    #[error("invalid effect state transition")]
    InvalidEffectTransition,
    #[error("invalid webhook event metadata")]
    InvalidWebhookMetadata,
}

#[cfg(test)]
mod tests {
    use razorproof_core::{Currency, MinorAmount, QuoteLine};

    use super::*;

    #[tokio::test]
    async fn effect_identity_replays_and_conflicts() -> Result<(), StoreError> {
        let store = Store::in_memory().await?;
        let tenant = TenantId::parse("merchant_a")?;
        let intent = IntentId::parse("intent_checkout_1")?;
        assert_eq!(
            store
                .claim_effect(&tenant, &intent, "create_order", "hash-a")
                .await?,
            EffectClaim::New
        );
        assert_eq!(
            store
                .claim_effect(&tenant, &intent, "create_order", "hash-a")
                .await?,
            EffectClaim::InFlight
        );
        assert_eq!(
            store
                .claim_effect(&tenant, &intent, "create_order", "hash-b")
                .await?,
            EffectClaim::Conflict
        );
        let response = serde_json::json!({"id_fingerprint":"abc"});
        store.complete_effect(&tenant, &intent, &response).await?;
        assert_eq!(
            store
                .claim_effect(&tenant, &intent, "create_order", "hash-a")
                .await?,
            EffectClaim::Replay { response }
        );
        Ok(())
    }

    #[tokio::test]
    async fn quote_cas_and_webhook_dedup_are_durable() -> Result<(), Box<dyn std::error::Error>> {
        let store = Store::in_memory().await?;
        let tenant = TenantId::parse("merchant_a")?;
        let mut quote = Quote::issue(
            tenant.clone(),
            Currency::parse("INR")?,
            vec![QuoteLine {
                sku: "sku_1".to_owned(),
                unit_amount: MinorAmount::new(201)?,
                quantity: 1,
            }],
            OffsetDateTime::now_utc() + time::Duration::minutes(5),
        )?;
        store.insert_quote(&quote).await?;
        let old_version = quote.version;
        quote.bind_order("order_1234567890", OffsetDateTime::now_utc())?;
        store.update_quote(&quote, old_version).await?;
        assert!(store.update_quote(&quote, old_version).await.is_err());
        assert!(
            !store
                .record_webhook(&tenant, "event-1", "payment.captured", b"{}")
                .await?
                .duplicate
        );
        assert!(
            store
                .record_webhook(&tenant, "event-1", "payment.captured", b"{}")
                .await?
                .duplicate
        );
        Ok(())
    }
}
