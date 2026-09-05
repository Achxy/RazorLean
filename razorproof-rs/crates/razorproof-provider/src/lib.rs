#![doc = "Tenant-isolated Razorpay HTTP adapter for RazorProof."]
// Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
// SPDX-License-Identifier: MIT
// Licensed under the MIT License. See LICENSE in the repository root.

use std::{collections::BTreeMap, sync::Arc, time::Duration};

use bytes::Bytes;
use percent_encoding::{AsciiSet, CONTROLS, utf8_percent_encode};
use razorproof_core::{IntentId, Quote};
use razorproof_policy::{Access, Idempotency, OperationCatalog, OperationSpec, PolicyError};
use reqwest::{Method, StatusCode, Url, header};
use secrecy::{ExposeSecret, SecretString};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use thiserror::Error;
use tokio::time::sleep;

const PATH_SEGMENT: &AsciiSet = &CONTROLS
    .add(b'/')
    .add(b'\\')
    .add(b'?')
    .add(b'#')
    .add(b'%')
    .add(b' ');
const MAX_RESPONSE_BYTES: usize = 2 * 1024 * 1024;
const MAX_DOCUMENT_BYTES: usize = 50_000 * 1024;

pub type QueryParameters = BTreeMap<String, Vec<String>>;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum NetworkMode {
    TestOnly,
    LiveAllowed,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum EndpointPolicy {
    OfficialOnly,
    AllowLoopback,
}

pub struct Credentials {
    key_id: SecretString,
    key_secret: SecretString,
}

impl Credentials {
    pub fn new(
        key_id: impl Into<String>,
        key_secret: impl Into<String>,
        mode: NetworkMode,
    ) -> Result<Self, ProviderError> {
        let key_id = key_id.into();
        let key_secret = key_secret.into();
        if key_id.len() < 12 || key_secret.len() < 16 {
            return Err(ProviderError::InvalidCredentials);
        }
        if mode == NetworkMode::TestOnly && !key_id.starts_with("rzp_test_") {
            return Err(ProviderError::LiveCredentialForbidden);
        }
        if !key_id
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_')
        {
            return Err(ProviderError::InvalidCredentials);
        }
        Ok(Self {
            key_id: SecretString::from(key_id),
            key_secret: SecretString::from(key_secret),
        })
    }

    #[must_use]
    pub fn is_test(&self) -> bool {
        self.key_id.expose_secret().starts_with("rzp_test_")
    }

    #[must_use]
    pub fn key_fingerprint(&self) -> String {
        blake3::hash(self.key_id.expose_secret().as_bytes()).to_hex()[..16].to_owned()
    }

    #[must_use]
    pub fn checkout_secret(&self) -> &[u8] {
        self.key_secret.expose_secret().as_bytes()
    }
}

impl std::fmt::Debug for Credentials {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("Credentials")
            .field("key_id", &"[REDACTED]")
            .field("key_secret", &"[REDACTED]")
            .finish()
    }
}

#[derive(Clone)]
pub struct RazorpayClient {
    http: reqwest::Client,
    base_url: Url,
    credentials: Arc<Credentials>,
    partner_account: Option<String>,
    catalog: Arc<OperationCatalog>,
}

impl RazorpayClient {
    pub fn new(
        credentials: Credentials,
        partner_account: Option<String>,
        base_url: Url,
        endpoint_policy: EndpointPolicy,
        catalog: Arc<OperationCatalog>,
    ) -> Result<Self, ProviderError> {
        validate_endpoint(&base_url, endpoint_policy)?;
        if let Some(account) = &partner_account {
            validate_provider_id(account, "acc_")?;
        }
        let http = reqwest::Client::builder()
            .connect_timeout(Duration::from_secs(5))
            .timeout(Duration::from_secs(20))
            .pool_idle_timeout(Duration::from_secs(30))
            .user_agent(concat!("razorproof/", env!("CARGO_PKG_VERSION")))
            .redirect(reqwest::redirect::Policy::none())
            .build()?;
        Ok(Self {
            http,
            base_url,
            credentials: Arc::new(credentials),
            partner_account,
            catalog,
        })
    }

    pub async fn execute(
        &self,
        operation_name: &str,
        path_parameters: &BTreeMap<String, String>,
        query: &QueryParameters,
        body: &Value,
        intent_id: Option<&IntentId>,
    ) -> Result<ProviderResponse, ProviderError> {
        let validated = self.catalog.validate_request(operation_name, body)?;
        let operation = validated.operation;
        if matches!(operation.access, Access::Local | Access::Ingress) {
            return Err(ProviderError::NoProviderTransport(operation.name));
        }
        if operation.access == Access::Write && intent_id.is_none() {
            return Err(ProviderError::IntentRequired(operation.name));
        }
        let method = Method::from_bytes(
            operation
                .method
                .as_deref()
                .ok_or_else(|| ProviderError::NoProviderTransport(operation.name.clone()))?
                .as_bytes(),
        )?;
        let path = render_path(
            operation
                .path
                .as_deref()
                .ok_or_else(|| ProviderError::NoProviderTransport(operation.name.clone()))?,
            path_parameters,
        )?;
        let url = build_url(&self.base_url, &operation.api_version, &path)?;
        let query = flatten_query(query)?;
        let max_attempts = if operation.idempotency == Idempotency::ReadOnly
            || operation.idempotency == Idempotency::RefundHeader
        {
            3
        } else {
            1
        };
        let mut last_error = None;
        for attempt in 1..=max_attempts {
            match self
                .send_once(
                    &operation,
                    method.clone(),
                    url.clone(),
                    &query,
                    body,
                    intent_id,
                )
                .await
            {
                Ok(response) if should_retry_status(response.status) && attempt < max_attempts => {
                    sleep(backoff(attempt)).await;
                }
                Ok(mut response) => {
                    response.attempts = attempt;
                    return Ok(response);
                }
                Err(error) if attempt < max_attempts && error.retryable() => {
                    last_error = Some(error);
                    sleep(backoff(attempt)).await;
                }
                Err(error) => return Err(error),
            }
        }
        Err(last_error.unwrap_or(ProviderError::RetryExhausted))
    }

    async fn send_once(
        &self,
        operation: &OperationSpec,
        method: Method,
        url: Url,
        query: &[(String, String)],
        body: &Value,
        intent_id: Option<&IntentId>,
    ) -> Result<ProviderResponse, ProviderError> {
        let mut request = self
            .http
            .request(method.clone(), url)
            .basic_auth(
                self.credentials.key_id.expose_secret(),
                Some(self.credentials.key_secret.expose_secret()),
            )
            .header(header::ACCEPT, "application/json")
            .query(query);
        if let Some(account) = &self.partner_account {
            request = request.header("X-Razorpay-Account", account);
        }
        if operation.idempotency == Idempotency::RefundHeader {
            let intent_id =
                intent_id.ok_or_else(|| ProviderError::IntentRequired(operation.name.clone()))?;
            request = request.header("X-Refund-Idempotency", intent_id.as_str());
        }
        if method != Method::GET && method != Method::HEAD {
            request = request.json(body);
        }
        let response = request.send().await?;
        let status = response.status();
        let request_id = response
            .headers()
            .get("x-request-id")
            .or_else(|| response.headers().get("x-razorpay-request-id"))
            .and_then(|value| value.to_str().ok())
            .map(ToOwned::to_owned);
        if response
            .content_length()
            .is_some_and(|length| length > MAX_RESPONSE_BYTES as u64)
        {
            return Err(ProviderError::ResponseTooLarge);
        }
        let bytes = response.bytes().await?;
        if bytes.len() > MAX_RESPONSE_BYTES {
            return Err(ProviderError::ResponseTooLarge);
        }
        let body = if bytes.is_empty() {
            Value::Null
        } else {
            serde_json::from_slice(&bytes).unwrap_or_else(|_| {
                serde_json::json!({
                    "non_json_body_hash": blake3::hash(&bytes).to_hex().to_string(),
                    "length": bytes.len()
                })
            })
        };
        Ok(ProviderResponse {
            status: status.as_u16(),
            request_id,
            body,
            attempts: 1,
        })
    }

    pub async fn upload_document(
        &self,
        upload: DocumentUpload,
        _intent_id: &IntentId,
    ) -> Result<ProviderResponse, ProviderError> {
        upload.validate()?;
        let url = self.base_url.join("documents")?;
        let mime = upload.detected_mime()?;
        let file_part = reqwest::multipart::Part::bytes(upload.bytes.to_vec())
            .file_name(upload.filename.clone())
            .mime_str(mime)?;
        let form = reqwest::multipart::Form::new()
            .text("purpose", upload.purpose)
            .part("file", file_part);
        let mut request = self
            .http
            .post(url)
            .basic_auth(
                self.credentials.key_id.expose_secret(),
                Some(self.credentials.key_secret.expose_secret()),
            )
            .header(header::ACCEPT, "application/json")
            .multipart(form);
        if let Some(account) = &self.partner_account {
            request = request.header("X-Razorpay-Account", account);
        }
        let response = request.send().await?;
        let status = response.status().as_u16();
        let bytes = response.bytes().await?;
        if bytes.len() > MAX_RESPONSE_BYTES {
            return Err(ProviderError::ResponseTooLarge);
        }
        let body = serde_json::from_slice(&bytes).unwrap_or_else(|_| {
            serde_json::json!({"non_json_body_hash": blake3::hash(&bytes).to_hex().to_string()})
        });
        Ok(ProviderResponse {
            status,
            request_id: None,
            body,
            attempts: 1,
        })
    }

    #[must_use]
    pub fn credentials(&self) -> &Credentials {
        &self.credentials
    }

    #[must_use]
    pub fn partner_account(&self) -> Option<&str> {
        self.partner_account.as_deref()
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct ProviderResponse {
    pub status: u16,
    pub request_id: Option<String>,
    pub body: Value,
    pub attempts: u8,
}

impl ProviderResponse {
    #[must_use]
    pub fn is_success(&self) -> bool {
        (200..300).contains(&self.status)
    }
}

#[derive(Clone, Debug)]
pub struct DocumentUpload {
    pub filename: String,
    pub purpose: String,
    pub bytes: Bytes,
}

impl DocumentUpload {
    pub fn validate(&self) -> Result<(), ProviderError> {
        if self.filename.is_empty()
            || self.filename.len() > 255
            || self.filename.contains('/')
            || self.filename.contains('\\')
            || self.bytes.is_empty()
            || self.bytes.len() > MAX_DOCUMENT_BYTES
        {
            return Err(ProviderError::InvalidDocument);
        }
        if self.purpose.is_empty()
            || self.purpose.len() > 64
            || !self
                .purpose
                .bytes()
                .all(|byte| byte.is_ascii_lowercase() || byte == b'_')
        {
            return Err(ProviderError::InvalidDocumentPurpose);
        }
        self.detected_mime()?;
        Ok(())
    }

    pub fn detected_mime(&self) -> Result<&'static str, ProviderError> {
        let sniffed = if self.bytes.starts_with(b"%PDF-") {
            "application/pdf"
        } else if self.bytes.starts_with(b"\x89PNG\r\n\x1a\n") {
            "image/png"
        } else if self.bytes.starts_with(&[0xff, 0xd8, 0xff]) {
            "image/jpeg"
        } else {
            return Err(ProviderError::UnsupportedDocumentType);
        };
        let extension = self
            .filename
            .rsplit_once('.')
            .map(|(_, extension)| extension.to_ascii_lowercase())
            .ok_or(ProviderError::UnsupportedDocumentType)?;
        let expected = match extension.as_str() {
            "pdf" => "application/pdf",
            "png" => "image/png",
            "jpg" | "jpeg" | "jfif" => "image/jpeg",
            _ => return Err(ProviderError::UnsupportedDocumentType),
        };
        if sniffed != expected {
            return Err(ProviderError::DocumentMimeMismatch);
        }
        Ok(sniffed)
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct ProviderOrderSnapshot {
    pub id: String,
    pub amount: i64,
    pub currency: String,
    pub status: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct ProviderPaymentSnapshot {
    pub id: String,
    pub order_id: String,
    pub amount: i64,
    pub currency: String,
    pub status: String,
}

pub fn verify_quote_binding(
    quote: &Quote,
    order: &ProviderOrderSnapshot,
    payment: &ProviderPaymentSnapshot,
) -> Result<(), ProviderError> {
    if order.id != payment.order_id
        || order.amount != quote.money.amount.get()
        || payment.amount != quote.money.amount.get()
        || order.currency != quote.money.currency.code()
        || payment.currency != quote.money.currency.code()
        || payment.status != "captured"
        || !matches!(order.status.as_str(), "paid" | "attempted")
    {
        return Err(ProviderError::QuoteBindingMismatch);
    }
    Ok(())
}

fn validate_endpoint(url: &Url, policy: EndpointPolicy) -> Result<(), ProviderError> {
    let official = url.scheme() == "https" && url.host_str() == Some("api.razorpay.com");
    let loopback = policy == EndpointPolicy::AllowLoopback
        && url.scheme() == "http"
        && matches!(url.host_str(), Some("127.0.0.1" | "localhost" | "[::1]"));
    if !official && !loopback {
        return Err(ProviderError::EndpointForbidden);
    }
    if url.path() != "/v1/" && url.path() != "/v1" {
        return Err(ProviderError::EndpointForbidden);
    }
    Ok(())
}

fn build_url(base_url: &Url, api_version: &str, path: &str) -> Result<Url, ProviderError> {
    if api_version == "v1" {
        return Ok(base_url.join(path.trim_start_matches('/'))?);
    }
    if api_version != "v2" {
        return Err(ProviderError::EndpointForbidden);
    }
    let mut origin = base_url.clone();
    origin.set_path("/");
    origin.set_query(None);
    origin.set_fragment(None);
    Ok(origin.join(&format!("v2/{}", path.trim_start_matches('/')))?)
}

fn validate_provider_id(value: &str, prefix: &str) -> Result<(), ProviderError> {
    if !value.starts_with(prefix)
        || value.len() > 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_')
    {
        return Err(ProviderError::InvalidProviderIdentifier);
    }
    Ok(())
}

fn render_path(
    template: &str,
    parameters: &BTreeMap<String, String>,
) -> Result<String, ProviderError> {
    let mut rendered = template.to_owned();
    for (name, value) in parameters {
        if name.is_empty()
            || !name
                .bytes()
                .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'_')
        {
            return Err(ProviderError::InvalidPathParameter);
        }
        if value.is_empty() || value.len() > 128 {
            return Err(ProviderError::InvalidPathParameter);
        }
        let placeholder = format!("{{{name}}}");
        if !rendered.contains(&placeholder) {
            return Err(ProviderError::UnexpectedPathParameter(name.clone()));
        }
        rendered = rendered.replace(
            &placeholder,
            &utf8_percent_encode(value, PATH_SEGMENT).to_string(),
        );
    }
    if rendered.contains('{') || rendered.contains('}') {
        return Err(ProviderError::MissingPathParameter(rendered));
    }
    Ok(rendered)
}

fn flatten_query(query: &QueryParameters) -> Result<Vec<(String, String)>, ProviderError> {
    let mut flattened = Vec::new();
    for (name, values) in query {
        if name.is_empty()
            || name.len() > 128
            || values.is_empty()
            || values.len() > 32
            || name.bytes().any(|byte| byte.is_ascii_control())
        {
            return Err(ProviderError::InvalidQueryParameter);
        }
        for value in values {
            if value.len() > 2_048 || value.bytes().any(|byte| byte.is_ascii_control()) {
                return Err(ProviderError::InvalidQueryParameter);
            }
            flattened.push((name.clone(), value.clone()));
        }
    }
    Ok(flattened)
}

fn should_retry_status(status: u16) -> bool {
    status == StatusCode::TOO_MANY_REQUESTS.as_u16() || (500..600).contains(&status)
}

fn backoff(attempt: u8) -> Duration {
    Duration::from_millis(100 * u64::from(attempt).pow(2))
}

#[derive(Debug, Error)]
pub enum ProviderError {
    #[error("invalid credentials")]
    InvalidCredentials,
    #[error("live credentials are forbidden in test-only mode")]
    LiveCredentialForbidden,
    #[error("provider endpoint is not an approved Razorpay or loopback endpoint")]
    EndpointForbidden,
    #[error("provider identifier is malformed")]
    InvalidProviderIdentifier,
    #[error("operation has no provider transport: {0}")]
    NoProviderTransport(String),
    #[error("a durable intent id is required for write operation {0}")]
    IntentRequired(String),
    #[error("invalid path parameter")]
    InvalidPathParameter,
    #[error("unexpected path parameter: {0}")]
    UnexpectedPathParameter(String),
    #[error("missing path parameter in {0}")]
    MissingPathParameter(String),
    #[error("query parameter is invalid")]
    InvalidQueryParameter,
    #[error("provider response exceeds the 2 MiB safety limit")]
    ResponseTooLarge,
    #[error("provider retries exhausted")]
    RetryExhausted,
    #[error("document upload is invalid")]
    InvalidDocument,
    #[error("document purpose is invalid")]
    InvalidDocumentPurpose,
    #[error("document type is unsupported")]
    UnsupportedDocumentType,
    #[error("document extension and magic bytes disagree")]
    DocumentMimeMismatch,
    #[error("provider order/payment do not match the server-authoritative quote")]
    QuoteBindingMismatch,
    #[error(transparent)]
    Policy(#[from] PolicyError),
    #[error(transparent)]
    Http(#[from] reqwest::Error),
    #[error(transparent)]
    HttpMethod(#[from] http::method::InvalidMethod),
    #[error(transparent)]
    Url(#[from] url::ParseError),
}

impl ProviderError {
    fn retryable(&self) -> bool {
        matches!(self, Self::Http(error) if error.is_connect() || error.is_timeout())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn test_catalog() -> Result<Arc<OperationCatalog>, ProviderError> {
        Ok(Arc::new(OperationCatalog::embedded()?))
    }

    #[test]
    fn refuses_live_credentials_and_unapproved_endpoints() -> Result<(), ProviderError> {
        assert!(
            Credentials::new(
                "rzp_live_123456789",
                "a-secret-that-is-long-enough",
                NetworkMode::TestOnly
            )
            .is_err()
        );
        let credentials = Credentials::new(
            "rzp_test_123456789",
            "a-secret-that-is-long-enough",
            NetworkMode::TestOnly,
        )?;
        assert!(
            RazorpayClient::new(
                credentials,
                None,
                Url::parse("https://evil.example/v1/")?,
                EndpointPolicy::OfficialOnly,
                test_catalog()?,
            )
            .is_err()
        );
        Ok(())
    }

    #[test]
    fn api_version_is_part_of_the_policy_not_caller_input() -> Result<(), ProviderError> {
        let base = Url::parse("https://api.razorpay.com/v1/")?;
        assert_eq!(
            build_url(&base, "v1", "/orders")?.as_str(),
            "https://api.razorpay.com/v1/orders"
        );
        assert_eq!(
            build_url(&base, "v2", "/accounts")?.as_str(),
            "https://api.razorpay.com/v2/accounts"
        );
        assert!(build_url(&base, "v3", "/accounts").is_err());
        Ok(())
    }

    #[test]
    fn document_magic_and_extension_must_match() {
        let upload = DocumentUpload {
            filename: "proof.png".to_owned(),
            purpose: "dispute_evidence".to_owned(),
            bytes: Bytes::from_static(b"%PDF-1.7\n"),
        };
        assert!(upload.validate().is_err());
        let png = DocumentUpload {
            filename: "proof.png".to_owned(),
            purpose: "dispute_evidence".to_owned(),
            bytes: Bytes::from_static(b"\x89PNG\r\n\x1a\nrest"),
        };
        assert!(matches!(png.detected_mime(), Ok("image/png")));
    }

    #[test]
    fn repeated_query_values_are_preserved() -> Result<(), ProviderError> {
        let flattened = flatten_query(&BTreeMap::from([(
            "expand[]".to_owned(),
            vec!["payments".to_owned(), "transfers".to_owned()],
        )]))?;
        assert_eq!(
            flattened,
            vec![
                ("expand[]".to_owned(), "payments".to_owned()),
                ("expand[]".to_owned(), "transfers".to_owned())
            ]
        );
        Ok(())
    }

    #[test]
    fn quote_binding_rejects_wrong_amount_or_uncaptured_payment()
    -> Result<(), Box<dyn std::error::Error>> {
        let quote = Quote::issue(
            razorproof_core::TenantId::parse("merchant_a")?,
            razorproof_core::Currency::parse("INR")?,
            vec![razorproof_core::QuoteLine {
                sku: "sku_1".to_owned(),
                unit_amount: razorproof_core::MinorAmount::new(201)?,
                quantity: 1,
            }],
            time::OffsetDateTime::now_utc() + time::Duration::minutes(5),
        )?;
        let order = ProviderOrderSnapshot {
            id: "order_1".to_owned(),
            amount: 201,
            currency: "INR".to_owned(),
            status: "paid".to_owned(),
        };
        let mut payment = ProviderPaymentSnapshot {
            id: "pay_1".to_owned(),
            order_id: "order_1".to_owned(),
            amount: 201,
            currency: "INR".to_owned(),
            status: "captured".to_owned(),
        };
        assert!(verify_quote_binding(&quote, &order, &payment).is_ok());
        payment.amount = 200;
        assert!(verify_quote_binding(&quote, &order, &payment).is_err());
        Ok(())
    }
}
