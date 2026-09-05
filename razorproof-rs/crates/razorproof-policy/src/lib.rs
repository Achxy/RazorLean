#![doc = "Policy catalog and semantic request validation for `RazorProof`."]
// Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
// SPDX-License-Identifier: MIT
// Licensed under the MIT License. See LICENSE in the repository root.

use std::collections::{BTreeMap, BTreeSet};

use razorproof_core::{Currency, Money, MoneyError, hash_canonical_json};
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use thiserror::Error;

const EMBEDDED_CATALOG: &str = include_str!("../../../policies/razorpay-operations.json");

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct OperationCatalog {
    pub catalog_version: String,
    pub upstream_mcp_commit: String,
    pub operations: Vec<OperationSpec>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct OperationSpec {
    pub name: String,
    #[serde(default)]
    pub aliases: Vec<String>,
    pub surface: String,
    pub access: Access,
    pub effect: Effect,
    #[serde(default = "default_api_version")]
    pub api_version: String,
    pub method: Option<String>,
    pub path: Option<String>,
    #[serde(default)]
    pub money_fields: Vec<String>,
    pub currency_field: Option<String>,
    pub idempotency: Idempotency,
    pub requires_quote: bool,
    pub source_tool: bool,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Access {
    Read,
    Write,
    Local,
    Ingress,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Effect {
    None,
    CaptureFunds,
    CreatePayment,
    CreateOrder,
    CreateCollectionSurface,
    RefundFunds,
    SettleFunds,
    CloseCollectionSurface,
    MetadataUpdate,
    Notification,
    CustomerAuthentication,
    TokenRevocation,
    GenerateCode,
    DocumentUpload,
    EventDelivery,
    CreateCustomer,
    CustomerStateChange,
    CreatePlan,
    SubscriptionStateChange,
    InvoiceStateChange,
    RouteTransfer,
    DisputeStateChange,
    VirtualAccountStateChange,
    PartnerOnboarding,
}

fn default_api_version() -> String {
    "v1".to_owned()
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Idempotency {
    ReadOnly,
    GatewayRequired,
    RefundHeader,
    EventId,
}

#[derive(Clone, Debug, Serialize)]
pub struct CoverageReport {
    pub catalog_operations: usize,
    pub upstream_tools: usize,
    pub covered_tools: usize,
    pub missing_from_catalog: Vec<String>,
    pub stale_catalog_tools: Vec<String>,
    pub duplicate_names: Vec<String>,
    pub complete: bool,
}

impl OperationCatalog {
    pub fn embedded() -> Result<Self, PolicyError> {
        let catalog: Self = serde_json::from_str(EMBEDDED_CATALOG)?;
        catalog.validate()?;
        Ok(catalog)
    }

    pub fn validate(&self) -> Result<(), PolicyError> {
        let mut names = BTreeSet::new();
        for operation in &self.operations {
            validate_token(&operation.name)?;
            if !names.insert(operation.name.clone()) {
                return Err(PolicyError::DuplicateOperation(operation.name.clone()));
            }
            for alias in &operation.aliases {
                validate_token(alias)?;
                if !names.insert(alias.clone()) {
                    return Err(PolicyError::DuplicateOperation(alias.clone()));
                }
            }
            if operation.access == Access::Write && operation.idempotency == Idempotency::ReadOnly {
                return Err(PolicyError::InvalidIdempotency(operation.name.clone()));
            }
            if operation.access == Access::Read
                && (operation.idempotency != Idempotency::ReadOnly
                    || operation.method.as_deref() != Some("GET"))
            {
                return Err(PolicyError::InvalidReadContract(operation.name.clone()));
            }
            match operation.access {
                Access::Read | Access::Write => {
                    let method = operation
                        .method
                        .as_deref()
                        .ok_or_else(|| PolicyError::InvalidTransport(operation.name.clone()))?;
                    let path = operation
                        .path
                        .as_deref()
                        .ok_or_else(|| PolicyError::InvalidTransport(operation.name.clone()))?;
                    if !matches!(method, "GET" | "POST" | "PUT" | "PATCH" | "DELETE")
                        || !path.starts_with('/')
                        || path.contains("://")
                        || path.contains('?')
                        || path.contains('#')
                        || path.contains("..")
                        || path.contains('\\')
                    {
                        return Err(PolicyError::InvalidTransport(operation.name.clone()));
                    }
                }
                Access::Local => {
                    if operation.method.is_some() || operation.path.is_some() {
                        return Err(PolicyError::InvalidTransport(operation.name.clone()));
                    }
                }
                Access::Ingress => {
                    if operation.path.is_some()
                        || operation.method.as_deref() != Some("POST")
                        || operation.idempotency != Idempotency::EventId
                    {
                        return Err(PolicyError::InvalidTransport(operation.name.clone()));
                    }
                }
            }
            if !matches!(operation.api_version.as_str(), "v1" | "v2") {
                return Err(PolicyError::InvalidApiVersion(operation.name.clone()));
            }
            for pointer in &operation.money_fields {
                if !pointer.starts_with('/') {
                    return Err(PolicyError::InvalidPointer(pointer.clone()));
                }
            }
            if operation
                .currency_field
                .as_deref()
                .is_some_and(|pointer| !pointer.starts_with('/'))
            {
                return Err(PolicyError::InvalidPointer(
                    operation.currency_field.clone().unwrap_or_default(),
                ));
            }
        }
        Ok(())
    }

    #[must_use]
    pub fn resolve(&self, name: &str) -> Option<&OperationSpec> {
        self.operations
            .iter()
            .find(|operation| operation.name == name || operation.aliases.iter().any(|a| a == name))
    }

    pub fn validate_request(
        &self,
        operation_name: &str,
        body: &Value,
    ) -> Result<ValidatedRequest, PolicyError> {
        let operation = self
            .resolve(operation_name)
            .ok_or_else(|| PolicyError::UnknownOperation(operation_name.to_owned()))?;
        validate_json_shape(body, 0, &mut 0)?;
        let currencies = match &operation.currency_field {
            Some(pointer) => pointer_values(body, pointer)?
                .into_iter()
                .map(|value| {
                    value
                        .as_str()
                        .ok_or_else(|| PolicyError::ExpectedCurrency(pointer.clone()))
                        .and_then(|value| Currency::parse(value).map_err(PolicyError::from))
                })
                .collect::<Result<Vec<_>, _>>()?,
            None => Vec::new(),
        };
        for pointer in &operation.money_fields {
            let amounts = pointer_values(body, pointer)?;
            if currencies.len() > 1 && currencies.len() != amounts.len() {
                return Err(PolicyError::CurrencyCardinality(pointer.clone()));
            }
            for (index, value) in amounts.into_iter().enumerate() {
                let amount = value
                    .as_i64()
                    .ok_or_else(|| PolicyError::FractionalOrUnsafeMoney(pointer.clone()))?;
                if let Some(currency) = currencies.get(index).or_else(|| currencies.first()) {
                    Money::from_minor(amount, currency.clone())?;
                } else {
                    // APIs such as refunds inherit currency from the addressed object. We can
                    // still prove that the outbound provider subunit is a positive exact integer;
                    // post-effect reconciliation proves its resource currency.
                    razorproof_core::MinorAmount::new(amount)?;
                }
            }
        }
        let body_hash = hash_canonical_json(body)?;
        Ok(ValidatedRequest {
            operation: operation.clone(),
            body_hash,
        })
    }

    pub fn audit_mcp_source(&self, source: &str) -> Result<CoverageReport, PolicyError> {
        let expression = Regex::new(r#"mcpgo\.NewTool\(\s*\"([^\"]+)\""#)
            .map_err(|error| PolicyError::Regex(error.to_string()))?;
        let upstream = expression
            .captures_iter(source)
            .filter_map(|capture| capture.get(1).map(|name| name.as_str().to_owned()))
            .collect::<BTreeSet<_>>();
        let catalog = self
            .operations
            .iter()
            .filter(|operation| operation.source_tool)
            .map(|operation| operation.name.clone())
            .collect::<BTreeSet<_>>();
        let missing_from_catalog = upstream.difference(&catalog).cloned().collect::<Vec<_>>();
        let stale_catalog_tools = catalog.difference(&upstream).cloned().collect::<Vec<_>>();
        let mut counts = BTreeMap::<String, usize>::new();
        for capture in expression.captures_iter(source) {
            if let Some(name) = capture.get(1) {
                *counts.entry(name.as_str().to_owned()).or_default() += 1;
            }
        }
        let duplicate_names = counts
            .into_iter()
            .filter_map(|(name, count)| (count > 1).then_some(name))
            .collect::<Vec<_>>();
        Ok(CoverageReport {
            catalog_operations: self.operations.len(),
            upstream_tools: upstream.len(),
            covered_tools: upstream.intersection(&catalog).count(),
            complete: missing_from_catalog.is_empty()
                && stale_catalog_tools.is_empty()
                && duplicate_names.is_empty(),
            missing_from_catalog,
            stale_catalog_tools,
            duplicate_names,
        })
    }
}

fn pointer_values<'a>(root: &'a Value, pointer: &str) -> Result<Vec<&'a Value>, PolicyError> {
    if !pointer.starts_with('/') {
        return Err(PolicyError::InvalidPointer(pointer.to_owned()));
    }
    let tokens = pointer[1..]
        .split('/')
        .map(|token| token.replace("~1", "/").replace("~0", "~"))
        .collect::<Vec<_>>();
    let mut current = vec![root];
    for token in tokens {
        let mut next = Vec::new();
        for value in current {
            if token == "*" {
                match value {
                    Value::Array(values) => next.extend(values),
                    Value::Object(values) => next.extend(values.values()),
                    _ => {}
                }
            } else {
                match value {
                    Value::Object(values) => {
                        if let Some(value) = values.get(&token) {
                            next.push(value);
                        }
                    }
                    Value::Array(values) => {
                        if let Ok(index) = token.parse::<usize>()
                            && let Some(value) = values.get(index)
                        {
                            next.push(value);
                        }
                    }
                    _ => {}
                }
            }
        }
        current = next;
    }
    Ok(current)
}

#[derive(Clone, Debug)]
pub struct ValidatedRequest {
    pub operation: OperationSpec,
    pub body_hash: String,
}

fn validate_token(value: &str) -> Result<(), PolicyError> {
    if value.is_empty()
        || value.len() > 96
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'_')
    {
        return Err(PolicyError::InvalidToken(value.to_owned()));
    }
    Ok(())
}

fn validate_json_shape(
    value: &Value,
    depth: usize,
    node_count: &mut usize,
) -> Result<(), PolicyError> {
    *node_count += 1;
    if depth > 24 || *node_count > 10_000 {
        return Err(PolicyError::BodyTooComplex);
    }
    match value {
        Value::String(value) if value.len() > 16_384 => return Err(PolicyError::StringTooLong),
        Value::Array(values) => {
            for value in values {
                validate_json_shape(value, depth + 1, node_count)?;
            }
        }
        Value::Object(values) => {
            for value in values.values() {
                validate_json_shape(value, depth + 1, node_count)?;
            }
        }
        _ => {}
    }
    Ok(())
}

#[derive(Debug, Error)]
pub enum PolicyError {
    #[error("unknown operation: {0}")]
    UnknownOperation(String),
    #[error("duplicate operation or alias: {0}")]
    DuplicateOperation(String),
    #[error("invalid operation token: {0}")]
    InvalidToken(String),
    #[error("write operation has read-only identity policy: {0}")]
    InvalidIdempotency(String),
    #[error("local operation declares a provider transport: {0}")]
    InvalidTransport(String),
    #[error("read operation must be a read-only GET: {0}")]
    InvalidReadContract(String),
    #[error("operation declares an unsupported API version: {0}")]
    InvalidApiVersion(String),
    #[error("invalid JSON pointer: {0}")]
    InvalidPointer(String),
    #[error("money at {0} must be a positive exact integer within the JSON safe range")]
    FractionalOrUnsafeMoney(String),
    #[error("expected ISO currency string at {0}")]
    ExpectedCurrency(String),
    #[error("currency values do not correspond to money values at {0}")]
    CurrencyCardinality(String),
    #[error("JSON body exceeds depth or node limits")]
    BodyTooComplex,
    #[error("JSON string exceeds 16384 bytes")]
    StringTooLong,
    #[error("source-parser regex failed: {0}")]
    Regex(String),
    #[error(transparent)]
    Json(#[from] serde_json::Error),
    #[error(transparent)]
    Money(#[from] MoneyError),
    #[error(transparent)]
    Evidence(#[from] razorproof_core::EvidenceError),
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn catalog_is_unique_and_broad() -> Result<(), PolicyError> {
        let catalog = OperationCatalog::embedded()?;
        assert_eq!(catalog.operations.len(), 113);
        assert_eq!(
            catalog
                .operations
                .iter()
                .filter(|operation| operation.source_tool)
                .count(),
            45
        );
        Ok(())
    }

    #[test]
    fn rejects_fractional_money_globally() -> Result<(), PolicyError> {
        let catalog = OperationCatalog::embedded()?;
        let result =
            catalog.validate_request("create_refund", &serde_json::json!({"amount": 100.75}));
        assert!(result.is_err());
        assert!(
            catalog
                .validate_request("create_refund", &serde_json::json!({"amount": 100}))
                .is_ok()
        );
        Ok(())
    }

    #[test]
    fn honors_zero_and_three_decimal_quantum() -> Result<(), PolicyError> {
        let catalog = OperationCatalog::embedded()?;
        assert!(
            catalog
                .validate_request(
                    "create_order",
                    &serde_json::json!({"amount": 295, "currency": "JPY"}),
                )
                .is_ok()
        );
        assert!(
            catalog
                .validate_request(
                    "create_order",
                    &serde_json::json!({"amount": 295991, "currency": "KWD"}),
                )
                .is_err()
        );
        Ok(())
    }

    #[test]
    fn wildcard_money_fields_remain_exact() -> Result<(), PolicyError> {
        let catalog = OperationCatalog::embedded()?;
        assert!(
            catalog
                .validate_request(
                    "create_invoice",
                    &serde_json::json!({
                        "currency": "INR",
                        "line_items": [{"amount": 100}, {"amount": 200}]
                    }),
                )
                .is_ok()
        );
        assert!(
            catalog
                .validate_request(
                    "create_invoice",
                    &serde_json::json!({
                        "currency": "INR",
                        "line_items": [{"amount": 100.75}]
                    }),
                )
                .is_err()
        );
        Ok(())
    }

    #[test]
    fn wildcard_currency_pairs_with_nested_amount() -> Result<(), PolicyError> {
        let catalog = OperationCatalog::embedded()?;
        assert!(
            catalog
                .validate_request(
                    "create_subscription",
                    &serde_json::json!({
                        "plan_id": "plan_example",
                        "addons": [
                            {"item": {"amount": 1000, "currency": "INR"}},
                            {"item": {"amount": 295990, "currency": "KWD"}}
                        ]
                    }),
                )
                .is_ok()
        );
        assert!(
            catalog
                .validate_request(
                    "create_subscription",
                    &serde_json::json!({
                        "plan_id": "plan_example",
                        "addons": [{"item": {"amount": 295991, "currency": "KWD"}}]
                    }),
                )
                .is_err()
        );
        Ok(())
    }

    #[test]
    fn legitimate_non_money_decimals_are_allowed() -> Result<(), PolicyError> {
        let catalog = OperationCatalog::embedded()?;
        assert!(
            catalog
                .validate_request(
                    "create_partner_stakeholder",
                    &serde_json::json!({"percentage_ownership": 87.55}),
                )
                .is_ok()
        );
        Ok(())
    }
}
