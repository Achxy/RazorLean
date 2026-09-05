#![doc = "Authenticated semantic firewall HTTP service for RazorProof."]
// Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
// SPDX-License-Identifier: MIT
// Licensed under the MIT License. See LICENSE in the repository root.

use std::{collections::BTreeMap, sync::Arc};

use axum::{
    Json, Router,
    body::Bytes,
    extract::{Path, State},
    http::{HeaderMap, HeaderName, StatusCode, header},
    response::{IntoResponse, Response},
    routing::{get, post},
};
use base64::{Engine as _, engine::general_purpose::STANDARD as BASE64};
use razorproof_core::{
    Currency, EvidenceKind, IntentId, MinorAmount, Quote, QuoteId, QuoteLine, QuoteState, TenantId,
    verify_checkout_signature, verify_webhook_signature,
};
use razorproof_policy::{Access, OperationCatalog};
use razorproof_provider::{
    Credentials, DocumentUpload, EndpointPolicy, NetworkMode, ProviderOrderSnapshot,
    ProviderPaymentSnapshot, ProviderResponse, QueryParameters, RazorpayClient,
    verify_quote_binding,
};
use razorproof_store::{EffectClaim, Store};
use secrecy::{ExposeSecret, SecretString};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use subtle::ConstantTimeEq;
use time::{Duration, OffsetDateTime};
use tower_http::{limit::RequestBodyLimitLayer, trace::TraceLayer};
use url::Url;

const MAX_JSON_BODY: usize = 1_048_576;
const MAX_WEBHOOK_BODY: usize = 1_048_576;

#[derive(Clone)]
pub struct AppState {
    store: Store,
    catalog: Arc<OperationCatalog>,
    tenants: Arc<BTreeMap<TenantId, TenantRuntime>>,
}

#[derive(Clone)]
struct TenantRuntime {
    gateway_token: Arc<SecretString>,
    webhook_secret: Arc<SecretString>,
    client: RazorpayClient,
}

pub struct TenantConfig {
    pub tenant_id: TenantId,
    pub gateway_token: String,
    pub webhook_secret: String,
    pub key_id: String,
    pub key_secret: String,
    pub partner_account: Option<String>,
}

impl AppState {
    pub fn single_tenant(store: Store, config: TenantConfig) -> Result<Self, ServerError> {
        let catalog = Arc::new(OperationCatalog::embedded()?);
        if config.gateway_token.len() < 24 || config.webhook_secret.len() < 16 {
            return Err(ServerError::WeakLocalSecret);
        }
        let credentials =
            Credentials::new(config.key_id, config.key_secret, NetworkMode::TestOnly)?;
        let client = RazorpayClient::new(
            credentials,
            config.partner_account,
            Url::parse("https://api.razorpay.com/v1/")?,
            EndpointPolicy::OfficialOnly,
            Arc::clone(&catalog),
        )?;
        let runtime = TenantRuntime {
            gateway_token: Arc::new(SecretString::from(config.gateway_token)),
            webhook_secret: Arc::new(SecretString::from(config.webhook_secret)),
            client,
        };
        Ok(Self {
            store,
            catalog,
            tenants: Arc::new(BTreeMap::from([(config.tenant_id, runtime)])),
        })
    }

    #[cfg(test)]
    fn with_client(
        store: Store,
        tenant_id: TenantId,
        gateway_token: String,
        webhook_secret: String,
        client: RazorpayClient,
        catalog: Arc<OperationCatalog>,
    ) -> Self {
        let runtime = TenantRuntime {
            gateway_token: Arc::new(SecretString::from(gateway_token)),
            webhook_secret: Arc::new(SecretString::from(webhook_secret)),
            client,
        };
        Self {
            store,
            catalog,
            tenants: Arc::new(BTreeMap::from([(tenant_id, runtime)])),
        }
    }
}

pub fn router(state: AppState) -> Router {
    Router::new()
        .route("/", get(index))
        .route("/assets/styles.css", get(styles))
        .route("/assets/app.js", get(script))
        .route("/healthz", get(health))
        .route("/v1/catalog", get(catalog))
        .route("/v1/quotes", post(create_quote))
        .route("/v1/quotes/{quote_id}", get(get_quote))
        .route("/v1/quotes/{quote_id}/order", post(create_order))
        .route("/v1/quotes/{quote_id}/verify", post(verify_payment))
        .route("/v1/quotes/{quote_id}/fulfill", post(fulfill))
        .route("/v1/operations/{operation}", post(execute_operation))
        .route("/v1/documents", post(upload_document))
        .route("/v1/evidence", get(list_evidence))
        .route(
            "/v1/webhooks/razorpay/{tenant_id}",
            post(receive_webhook).layer(RequestBodyLimitLayer::new(MAX_WEBHOOK_BODY)),
        )
        .layer(RequestBodyLimitLayer::new(MAX_JSON_BODY))
        .layer(TraceLayer::new_for_http())
        .with_state(state)
}

async fn index() -> Response {
    (
        [
            (header::CONTENT_TYPE, "text/html; charset=utf-8"),
            (
                HeaderName::from_static("content-security-policy"),
                "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
            ),
            (
                HeaderName::from_static("permissions-policy"),
                "camera=(), microphone=(), geolocation=(), payment=()",
            ),
            (HeaderName::from_static("referrer-policy"), "no-referrer"),
            (
                HeaderName::from_static("x-content-type-options"),
                "nosniff",
            ),
            (HeaderName::from_static("x-frame-options"), "DENY"),
            (
                HeaderName::from_static("cross-origin-resource-policy"),
                "same-origin",
            ),
            (header::CACHE_CONTROL, "no-store"),
        ],
        include_str!("../assets/index.html"),
    )
        .into_response()
}

async fn styles() -> Response {
    embedded_asset(
        "text/css; charset=utf-8",
        include_str!("../assets/styles.css"),
    )
}

async fn script() -> Response {
    embedded_asset(
        "text/javascript; charset=utf-8",
        include_str!("../assets/app.js"),
    )
}

fn embedded_asset(content_type: &'static str, body: &'static str) -> Response {
    (
        [
            (header::CONTENT_TYPE, content_type),
            (HeaderName::from_static("x-content-type-options"), "nosniff"),
            (
                HeaderName::from_static("cross-origin-resource-policy"),
                "same-origin",
            ),
            (header::CACHE_CONTROL, "no-cache"),
        ],
        body,
    )
        .into_response()
}

async fn health(State(state): State<AppState>) -> Result<Json<Value>, ApiError> {
    state.store.health().await.map_err(ApiError::internal)?;
    Ok(Json(json!({
        "status": "ok",
        "mode": "test_only",
        "catalog_version": state.catalog.catalog_version,
        "operation_count": state.catalog.operations.len()
    })))
}

async fn catalog(
    State(state): State<AppState>,
    headers: HeaderMap,
) -> Result<Json<Value>, ApiError> {
    authenticate(&state, &headers)?;
    Ok(Json(
        serde_json::to_value(state.catalog.as_ref()).map_err(ApiError::internal)?,
    ))
}

#[derive(Debug, Deserialize)]
struct CreateQuoteRequest {
    currency: String,
    lines: Vec<CreateQuoteLine>,
    #[serde(default = "default_quote_ttl")]
    ttl_seconds: u32,
}

#[derive(Debug, Deserialize)]
struct CreateQuoteLine {
    sku: String,
    unit_amount_minor: i64,
    quantity: u32,
}

const fn default_quote_ttl() -> u32 {
    900
}

async fn create_quote(
    State(state): State<AppState>,
    headers: HeaderMap,
    Json(request): Json<CreateQuoteRequest>,
) -> Result<(StatusCode, Json<Quote>), ApiError> {
    let (tenant_id, _) = authenticate(&state, &headers)?;
    if !(60..=3_600).contains(&request.ttl_seconds) {
        return Err(ApiError::bad_request(
            "invalid_quote_ttl",
            "quote TTL must be 60 to 3600 seconds",
        ));
    }
    let currency = Currency::parse(request.currency).map_err(ApiError::bad_input)?;
    let lines = request
        .lines
        .into_iter()
        .map(|line| {
            Ok(QuoteLine {
                sku: line.sku,
                unit_amount: MinorAmount::new(line.unit_amount_minor)
                    .map_err(ApiError::bad_input)?,
                quantity: line.quantity,
            })
        })
        .collect::<Result<Vec<_>, ApiError>>()?;
    let quote = Quote::issue(
        tenant_id.clone(),
        currency,
        lines,
        OffsetDateTime::now_utc() + Duration::seconds(i64::from(request.ttl_seconds)),
    )
    .map_err(ApiError::bad_input)?;
    state
        .store
        .insert_quote(&quote)
        .await
        .map_err(ApiError::internal)?;
    state
        .store
        .append_evidence(
            tenant_id,
            EvidenceKind::StateTransition,
            "issue_quote",
            quote.id.as_str().as_bytes(),
            &json!({
                "quote_id": quote.id.as_str(),
                "amount": quote.money.amount.get(),
                "currency": quote.money.currency.code(),
                "cart_hash": quote.cart_hash
            }),
        )
        .await
        .map_err(ApiError::internal)?;
    Ok((StatusCode::CREATED, Json(quote)))
}

async fn get_quote(
    State(state): State<AppState>,
    headers: HeaderMap,
    Path(quote_id): Path<String>,
) -> Result<Json<Quote>, ApiError> {
    let (tenant_id, _) = authenticate(&state, &headers)?;
    Ok(Json(load_quote(&state, &tenant_id, &quote_id).await?))
}

#[derive(Debug, Default, Deserialize)]
struct CreateOrderRequest {
    #[serde(default)]
    notes: BTreeMap<String, String>,
}

async fn create_order(
    State(state): State<AppState>,
    headers: HeaderMap,
    Path(quote_id): Path<String>,
    Json(request): Json<CreateOrderRequest>,
) -> Result<Json<Value>, ApiError> {
    let (tenant_id, runtime) = authenticate(&state, &headers)?;
    let intent = required_intent(&headers)?;
    let mut quote = load_quote(&state, &tenant_id, &quote_id).await?;
    if let QuoteState::OrderBound { provider_order_id } = &quote.state {
        return Ok(Json(json!({
            "quote": quote,
            "provider": {
                "replayed": true,
                "body": {"id": provider_order_id}
            }
        })));
    }
    if !matches!(quote.state, QuoteState::Issued) {
        return Err(ApiError::conflict(
            "quote_state_conflict",
            "quote cannot create another order",
        ));
    }
    let mut notes = request.notes;
    notes.insert("razorproof_quote".to_owned(), quote.id.as_str().to_owned());
    notes.insert("razorproof_cart_hash".to_owned(), quote.cart_hash.clone());
    let receipt = format!("rp_{}", &quote.cart_hash[..32]);
    let body = json!({
        "amount": quote.money.amount.get(),
        "currency": quote.money.currency.code(),
        "receipt": receipt,
        "notes": notes
    });
    let response = execute_guarded(
        &state,
        &tenant_id,
        runtime,
        "create_order",
        BTreeMap::new(),
        BTreeMap::new(),
        body,
        Some(intent),
        Some(&quote),
    )
    .await?;
    ensure_provider_success(&response)?;
    let order_id = response
        .body
        .get("id")
        .and_then(Value::as_str)
        .ok_or_else(|| ApiError::bad_gateway("provider_contract", "order response omitted id"))?;
    let expected_version = quote.version;
    quote
        .bind_order(order_id, OffsetDateTime::now_utc())
        .map_err(ApiError::conflict_input)?;
    state
        .store
        .update_quote(&quote, expected_version)
        .await
        .map_err(ApiError::store_conflict)?;
    append_transition(&state, &quote, "bind_order").await?;
    Ok(Json(json!({"quote": quote, "provider": response})))
}

#[derive(Debug, Deserialize)]
struct VerifyPaymentRequest {
    payment_id: String,
    signature: String,
}

async fn verify_payment(
    State(state): State<AppState>,
    headers: HeaderMap,
    Path(quote_id): Path<String>,
    Json(request): Json<VerifyPaymentRequest>,
) -> Result<Json<Quote>, ApiError> {
    let (tenant_id, runtime) = authenticate(&state, &headers)?;
    let mut quote = load_quote(&state, &tenant_id, &quote_id).await?;
    let provider_order_id = match &quote.state {
        QuoteState::OrderBound { provider_order_id } => provider_order_id.clone(),
        _ => {
            return Err(ApiError::conflict(
                "quote_state_conflict",
                "quote is not bound to an order",
            ));
        }
    };
    verify_checkout_signature(
        &provider_order_id,
        &request.payment_id,
        &request.signature,
        runtime.client.credentials().checkout_secret(),
    )
    .map_err(|_| ApiError::unauthorized("invalid_checkout_signature"))?;

    let order_response = runtime
        .client
        .execute(
            "fetch_order",
            &BTreeMap::from([("order_id".to_owned(), provider_order_id.clone())]),
            &BTreeMap::new(),
            &Value::Null,
            None,
        )
        .await
        .map_err(ApiError::provider_transport)?;
    let payment_response = runtime
        .client
        .execute(
            "fetch_payment",
            &BTreeMap::from([("payment_id".to_owned(), request.payment_id.clone())]),
            &BTreeMap::new(),
            &Value::Null,
            None,
        )
        .await
        .map_err(ApiError::provider_transport)?;
    ensure_provider_success(&order_response)?;
    ensure_provider_success(&payment_response)?;
    let order: ProviderOrderSnapshot =
        serde_json::from_value(order_response.body).map_err(ApiError::provider_contract)?;
    let payment: ProviderPaymentSnapshot =
        serde_json::from_value(payment_response.body).map_err(ApiError::provider_contract)?;
    verify_quote_binding(&quote, &order, &payment).map_err(|_| {
        ApiError::conflict(
            "economic_binding_failed",
            "provider state does not match the quote",
        )
    })?;
    let expected_version = quote.version;
    quote
        .verify_payment(
            &provider_order_id,
            request.payment_id,
            OffsetDateTime::now_utc(),
        )
        .map_err(ApiError::conflict_input)?;
    state
        .store
        .update_quote(&quote, expected_version)
        .await
        .map_err(ApiError::store_conflict)?;
    append_transition(&state, &quote, "verify_payment").await?;
    Ok(Json(quote))
}

#[derive(Debug, Deserialize)]
struct FulfillRequest {
    reference: String,
}

async fn fulfill(
    State(state): State<AppState>,
    headers: HeaderMap,
    Path(quote_id): Path<String>,
    Json(request): Json<FulfillRequest>,
) -> Result<Json<Quote>, ApiError> {
    let (tenant_id, _) = authenticate(&state, &headers)?;
    let intent = required_intent(&headers)?;
    let mut quote = load_quote(&state, &tenant_id, &quote_id).await?;
    if let QuoteState::Fulfilled {
        fulfillment_reference,
        ..
    } = &quote.state
    {
        return if fulfillment_reference == &request.reference {
            Ok(Json(quote))
        } else {
            Err(ApiError::conflict(
                "already_fulfilled",
                "quote was fulfilled with a different reference",
            ))
        };
    }
    let body = json!({"quote_id": quote.id.as_str(), "reference": request.reference});
    let body_hash = razorproof_core::hash_canonical_json(&body).map_err(ApiError::internal)?;
    match state
        .store
        .claim_effect(&tenant_id, &intent, "fulfill", &body_hash)
        .await
        .map_err(ApiError::internal)?
    {
        EffectClaim::New => {}
        EffectClaim::Replay { .. } => return Ok(Json(quote)),
        EffectClaim::InFlight => {
            return Err(ApiError::conflict(
                "intent_in_flight",
                "intent is already in flight",
            ));
        }
        EffectClaim::Conflict => {
            return Err(ApiError::conflict(
                "intent_reused",
                "intent was reused with different input",
            ));
        }
        EffectClaim::PriorFailure => {
            return Err(ApiError::conflict(
                "intent_failed",
                "intent requires reconciliation",
            ));
        }
    }
    let expected_version = quote.version;
    quote
        .fulfill(request.reference)
        .map_err(ApiError::conflict_input)?;
    state
        .store
        .update_quote(&quote, expected_version)
        .await
        .map_err(ApiError::store_conflict)?;
    let serialized = serde_json::to_value(&quote).map_err(ApiError::internal)?;
    state
        .store
        .complete_effect(&tenant_id, &intent, &serialized)
        .await
        .map_err(ApiError::internal)?;
    append_transition(&state, &quote, "fulfill").await?;
    Ok(Json(quote))
}

#[derive(Debug, Default, Deserialize)]
struct OperationRequest {
    #[serde(default)]
    path: BTreeMap<String, String>,
    #[serde(default)]
    query: QueryParameters,
    #[serde(default)]
    body: Value,
    quote_id: Option<String>,
}

async fn execute_operation(
    State(state): State<AppState>,
    headers: HeaderMap,
    Path(operation): Path<String>,
    Json(request): Json<OperationRequest>,
) -> Result<Json<Value>, ApiError> {
    let (tenant_id, runtime) = authenticate(&state, &headers)?;
    let spec = state.catalog.resolve(&operation).ok_or_else(|| {
        ApiError::not_found("unknown_operation", "operation is not in the catalog")
    })?;
    if matches!(spec.access, Access::Local | Access::Ingress) || operation == "create_document" {
        return Err(ApiError::bad_request(
            "wrong_surface",
            "operation uses a dedicated local or ingress surface",
        ));
    }
    let quote = if spec.requires_quote {
        let quote_id = request.quote_id.as_deref().ok_or_else(|| {
            ApiError::bad_request("quote_required", "operation requires a server quote")
        })?;
        Some(load_quote(&state, &tenant_id, quote_id).await?)
    } else {
        None
    };
    let intent = if spec.access == Access::Write {
        Some(required_intent(&headers)?)
    } else {
        None
    };
    let response = execute_guarded(
        &state,
        &tenant_id,
        runtime,
        &operation,
        request.path,
        request.query,
        request.body,
        intent,
        quote.as_ref(),
    )
    .await?;
    Ok(Json(json!({"provider": response})))
}

#[derive(Debug, Deserialize)]
struct UploadDocumentRequest {
    filename: String,
    purpose: String,
    content_base64: String,
}

async fn upload_document(
    State(state): State<AppState>,
    headers: HeaderMap,
    Json(request): Json<UploadDocumentRequest>,
) -> Result<Json<Value>, ApiError> {
    let (tenant_id, runtime) = authenticate(&state, &headers)?;
    let intent = required_intent(&headers)?;
    let bytes = BASE64
        .decode(request.content_base64.as_bytes())
        .map_err(|_| {
            ApiError::bad_request("invalid_base64", "document content is not valid base64")
        })?;
    let summary = json!({
        "filename": request.filename,
        "purpose": request.purpose,
        "content_hash": blake3::hash(&bytes).to_hex().to_string(),
        "content_length": bytes.len()
    });
    let body_hash = razorproof_core::hash_canonical_json(&summary).map_err(ApiError::internal)?;
    match state
        .store
        .claim_effect(&tenant_id, &intent, "create_document", &body_hash)
        .await
        .map_err(ApiError::internal)?
    {
        EffectClaim::Replay { response } => return Ok(Json(response)),
        EffectClaim::New => {}
        EffectClaim::InFlight => {
            return Err(ApiError::conflict(
                "intent_in_flight",
                "intent is already in flight",
            ));
        }
        EffectClaim::Conflict => {
            return Err(ApiError::conflict(
                "intent_reused",
                "intent was reused with different input",
            ));
        }
        EffectClaim::PriorFailure => {
            return Err(ApiError::conflict(
                "intent_failed",
                "intent requires reconciliation",
            ));
        }
    }
    let upload = DocumentUpload {
        filename: summary["filename"].as_str().unwrap_or_default().to_owned(),
        purpose: summary["purpose"].as_str().unwrap_or_default().to_owned(),
        bytes: bytes.into(),
    };
    let response = match runtime.client.upload_document(upload, &intent).await {
        Ok(response) => response,
        Err(error) => {
            state
                .store
                .fail_effect(&tenant_id, &intent, "provider_transport_ambiguous")
                .await
                .map_err(ApiError::internal)?;
            return Err(ApiError::provider_transport(error));
        }
    };
    let value = serde_json::to_value(&response).map_err(ApiError::internal)?;
    state
        .store
        .complete_effect(&tenant_id, &intent, &value)
        .await
        .map_err(ApiError::internal)?;
    state
        .store
        .append_evidence(
            tenant_id,
            EvidenceKind::ProviderResponse,
            "create_document",
            intent.as_str().as_bytes(),
            &json!({"status": response.status, "body_hash": body_hash}),
        )
        .await
        .map_err(ApiError::internal)?;
    Ok(Json(value))
}

async fn receive_webhook(
    State(state): State<AppState>,
    Path(tenant_id): Path<String>,
    headers: HeaderMap,
    body: Bytes,
) -> Result<Json<Value>, ApiError> {
    let tenant_id = TenantId::parse(tenant_id).map_err(ApiError::bad_input)?;
    let runtime = state
        .tenants
        .get(&tenant_id)
        .ok_or_else(|| ApiError::not_found("unknown_tenant", "tenant is not configured"))?;
    let signature = required_header(&headers, "x-razorpay-signature")?;
    let event_id = required_header(&headers, "x-razorpay-event-id")?;
    verify_webhook_signature(
        &body,
        signature,
        runtime.webhook_secret.expose_secret().as_bytes(),
    )
    .map_err(|_| ApiError::unauthorized("invalid_webhook_signature"))?;
    let payload: Value = serde_json::from_slice(&body).map_err(|_| {
        ApiError::bad_request("invalid_webhook_json", "webhook body is not valid JSON")
    })?;
    let event_type = payload
        .get("event")
        .and_then(Value::as_str)
        .ok_or_else(|| ApiError::bad_request("missing_event_type", "webhook omitted event"))?;
    let receipt = state
        .store
        .record_webhook(&tenant_id, event_id, event_type, &body)
        .await
        .map_err(ApiError::internal)?;
    let kind = if receipt.duplicate {
        EvidenceKind::WebhookDuplicate
    } else {
        EvidenceKind::WebhookAccepted
    };
    state
        .store
        .append_evidence(
            tenant_id,
            kind,
            event_type,
            event_id.as_bytes(),
            &json!({
                "body_hash": receipt.body_hash,
                "duplicate": receipt.duplicate,
                "event_id_fingerprint": receipt.event_id_fingerprint
            }),
        )
        .await
        .map_err(ApiError::internal)?;
    Ok(Json(
        json!({"accepted": true, "duplicate": receipt.duplicate}),
    ))
}

async fn list_evidence(
    State(state): State<AppState>,
    headers: HeaderMap,
) -> Result<Json<Value>, ApiError> {
    let (tenant_id, _) = authenticate(&state, &headers)?;
    let events = state
        .store
        .list_evidence(&tenant_id, 200)
        .await
        .map_err(ApiError::internal)?;
    Ok(Json(json!({"events": events})))
}

#[allow(clippy::too_many_arguments)]
async fn execute_guarded(
    state: &AppState,
    tenant_id: &TenantId,
    runtime: &TenantRuntime,
    operation: &str,
    path: BTreeMap<String, String>,
    query: QueryParameters,
    body: Value,
    intent: Option<IntentId>,
    quote: Option<&Quote>,
) -> Result<ProviderResponse, ApiError> {
    let validated = state
        .catalog
        .validate_request(operation, &body)
        .map_err(ApiError::bad_input)?;
    if validated.operation.requires_quote {
        enforce_quote_binding(
            quote,
            &validated.operation.money_fields,
            &validated.operation.currency_field,
            &body,
        )?;
    }

    if validated.operation.access == Access::Write {
        let intent = intent.as_ref().ok_or_else(|| {
            ApiError::bad_request("intent_required", "write operation requires an intent")
        })?;
        match state
            .store
            .claim_effect(
                tenant_id,
                intent,
                &validated.operation.name,
                &validated.body_hash,
            )
            .await
            .map_err(ApiError::internal)?
        {
            EffectClaim::Replay { response } => {
                return serde_json::from_value(response).map_err(ApiError::internal);
            }
            EffectClaim::New => {}
            EffectClaim::InFlight => {
                return Err(ApiError::conflict(
                    "intent_in_flight",
                    "intent is already in flight",
                ));
            }
            EffectClaim::Conflict => {
                return Err(ApiError::conflict(
                    "intent_reused",
                    "intent was reused with different input",
                ));
            }
            EffectClaim::PriorFailure => {
                return Err(ApiError::conflict(
                    "intent_failed",
                    "intent requires reconciliation",
                ));
            }
        }
        state
            .store
            .append_evidence(
                tenant_id.clone(),
                EvidenceKind::RequestAccepted,
                &validated.operation.name,
                intent.as_str().as_bytes(),
                &json!({"body_hash": validated.body_hash}),
            )
            .await
            .map_err(ApiError::internal)?;
    }

    let response = match runtime
        .client
        .execute(operation, &path, &query, &body, intent.as_ref())
        .await
    {
        Ok(response) => response,
        Err(error) => {
            if let Some(intent) = &intent {
                state
                    .store
                    .fail_effect(tenant_id, intent, "provider_transport_ambiguous")
                    .await
                    .map_err(ApiError::internal)?;
            }
            return Err(ApiError::provider_transport(error));
        }
    };
    if validated.operation.access == Access::Write && response.status >= 500 {
        if let Some(intent) = &intent {
            state
                .store
                .fail_effect(tenant_id, intent, "provider_server_error_ambiguous")
                .await
                .map_err(ApiError::internal)?;
        }
        state
            .store
            .append_evidence(
                tenant_id.clone(),
                EvidenceKind::RequestRejected,
                &validated.operation.name,
                intent
                    .as_ref()
                    .map_or(validated.body_hash.as_bytes(), |value| {
                        value.as_str().as_bytes()
                    }),
                &json!({"status": response.status, "ambiguous": true}),
            )
            .await
            .map_err(ApiError::internal)?;
        return Err(ApiError::new(
            StatusCode::SERVICE_UNAVAILABLE,
            "provider_result_ambiguous",
            "provider returned a server error; reconcile the intent before retrying",
        ));
    }
    if let Some(intent) = &intent {
        let value = serde_json::to_value(&response).map_err(ApiError::internal)?;
        state
            .store
            .complete_effect(tenant_id, intent, &value)
            .await
            .map_err(ApiError::internal)?;
    }
    state
        .store
        .append_evidence(
            tenant_id.clone(),
            EvidenceKind::ProviderResponse,
            &validated.operation.name,
            intent
                .as_ref()
                .map_or(validated.body_hash.as_bytes(), |value| value.as_str().as_bytes()),
            &json!({
                "status": response.status,
                "attempts": response.attempts,
                "request_id_fingerprint": response.request_id.as_ref().map(|value| blake3::hash(value.as_bytes()).to_hex()[..16].to_owned())
            }),
        )
        .await
        .map_err(ApiError::internal)?;
    Ok(response)
}

fn enforce_quote_binding(
    quote: Option<&Quote>,
    money_fields: &[String],
    currency_field: &Option<String>,
    body: &Value,
) -> Result<(), ApiError> {
    let quote = quote
        .ok_or_else(|| ApiError::bad_request("quote_required", "operation requires a quote"))?;
    if !matches!(
        quote.state,
        QuoteState::Issued | QuoteState::OrderBound { .. }
    ) {
        return Err(ApiError::conflict(
            "quote_state_conflict",
            "quote cannot authorize this operation",
        ));
    }
    let quote_amount_pointer = money_fields.first().ok_or_else(|| {
        ApiError::bad_request("policy_error", "quoted operation has no amount field")
    })?;
    let amount = body
        .pointer(quote_amount_pointer)
        .and_then(Value::as_i64)
        .ok_or_else(|| {
            ApiError::bad_request("quoted_amount_required", "quoted amount must be present")
        })?;
    if amount != quote.money.amount.get() {
        return Err(ApiError::conflict(
            "quoted_amount_mismatch",
            "request amount differs from the server quote",
        ));
    }
    if let Some(pointer) = currency_field {
        let currency = body
            .pointer(pointer)
            .and_then(Value::as_str)
            .ok_or_else(|| {
                ApiError::bad_request("quoted_currency_required", "currency must be present")
            })?;
        if currency != quote.money.currency.code() {
            return Err(ApiError::conflict(
                "quoted_currency_mismatch",
                "request currency differs from the server quote",
            ));
        }
    }
    Ok(())
}

fn authenticate<'a>(
    state: &'a AppState,
    headers: &HeaderMap,
) -> Result<(TenantId, &'a TenantRuntime), ApiError> {
    let tenant_id = TenantId::parse(required_header(headers, "x-razorproof-tenant")?)
        .map_err(ApiError::bad_input)?;
    let runtime = state
        .tenants
        .get(&tenant_id)
        .ok_or_else(|| ApiError::unauthorized("authentication_failed"))?;
    let authorization = required_header(headers, header::AUTHORIZATION.as_str())?;
    let token = authorization
        .strip_prefix("Bearer ")
        .ok_or_else(|| ApiError::unauthorized("authentication_failed"))?;
    let expected = runtime.gateway_token.expose_secret().as_bytes();
    let valid = token.as_bytes().len() == expected.len() && token.as_bytes().ct_eq(expected).into();
    if !valid {
        return Err(ApiError::unauthorized("authentication_failed"));
    }
    Ok((tenant_id, runtime))
}

fn required_header<'a>(headers: &'a HeaderMap, name: &str) -> Result<&'a str, ApiError> {
    headers
        .get(name)
        .and_then(|value| value.to_str().ok())
        .filter(|value| !value.is_empty())
        .ok_or_else(|| {
            ApiError::bad_request(
                "missing_header",
                format!("required header {name} is missing"),
            )
        })
}

fn required_intent(headers: &HeaderMap) -> Result<IntentId, ApiError> {
    IntentId::parse(required_header(headers, "x-razorproof-intent")?).map_err(ApiError::bad_input)
}

async fn load_quote(
    state: &AppState,
    tenant_id: &TenantId,
    quote_id: &str,
) -> Result<Quote, ApiError> {
    let quote_id = QuoteId::parse(quote_id).map_err(ApiError::bad_input)?;
    state
        .store
        .get_quote(tenant_id, &quote_id)
        .await
        .map_err(ApiError::internal)?
        .ok_or_else(|| ApiError::not_found("quote_not_found", "quote does not exist"))
}

async fn append_transition(
    state: &AppState,
    quote: &Quote,
    operation: &str,
) -> Result<(), ApiError> {
    state
        .store
        .append_evidence(
            quote.tenant_id.clone(),
            EvidenceKind::StateTransition,
            operation,
            quote.id.as_str().as_bytes(),
            &json!({"quote_id": quote.id.as_str(), "version": quote.version, "state": quote.state}),
        )
        .await
        .map_err(ApiError::internal)?;
    Ok(())
}

fn ensure_provider_success(response: &ProviderResponse) -> Result<(), ApiError> {
    if response.is_success() {
        Ok(())
    } else {
        Err(ApiError::bad_gateway(
            "provider_rejected",
            format!("Razorpay returned HTTP {}", response.status),
        ))
    }
}

#[derive(Debug, Serialize)]
struct Problem {
    #[serde(rename = "type")]
    problem_type: String,
    title: String,
    status: u16,
    code: String,
    detail: String,
}

#[derive(Debug)]
struct ApiError {
    status: StatusCode,
    code: String,
    detail: String,
}

impl ApiError {
    fn new(status: StatusCode, code: impl Into<String>, detail: impl Into<String>) -> Self {
        Self {
            status,
            code: code.into(),
            detail: detail.into(),
        }
    }

    fn bad_request(code: impl Into<String>, detail: impl Into<String>) -> Self {
        Self::new(StatusCode::BAD_REQUEST, code, detail)
    }

    fn bad_input(error: impl std::fmt::Display) -> Self {
        Self::bad_request("semantic_validation_failed", error.to_string())
    }

    fn conflict(code: impl Into<String>, detail: impl Into<String>) -> Self {
        Self::new(StatusCode::CONFLICT, code, detail)
    }

    fn conflict_input(error: impl std::fmt::Display) -> Self {
        Self::conflict("state_transition_rejected", error.to_string())
    }

    fn not_found(code: impl Into<String>, detail: impl Into<String>) -> Self {
        Self::new(StatusCode::NOT_FOUND, code, detail)
    }

    fn unauthorized(code: impl Into<String>) -> Self {
        Self::new(StatusCode::UNAUTHORIZED, code, "authentication failed")
    }

    fn bad_gateway(code: impl Into<String>, detail: impl Into<String>) -> Self {
        Self::new(StatusCode::BAD_GATEWAY, code, detail)
    }

    fn provider_contract(error: impl std::fmt::Display) -> Self {
        Self::bad_gateway("provider_contract", error.to_string())
    }

    fn provider_transport(error: impl std::fmt::Display) -> Self {
        tracing::warn!(error = %error, "Razorpay transport failed");
        Self::new(
            StatusCode::SERVICE_UNAVAILABLE,
            "provider_transport_ambiguous",
            "provider result is unknown; reconcile before retrying",
        )
    }

    fn internal(error: impl std::fmt::Display) -> Self {
        tracing::error!(error = %error, "internal RazorProof failure");
        Self::new(
            StatusCode::INTERNAL_SERVER_ERROR,
            "internal_error",
            "request could not be completed",
        )
    }

    fn store_conflict(error: impl std::fmt::Display) -> Self {
        tracing::warn!(error = %error, "state write conflict");
        Self::conflict(
            "concurrent_state_change",
            "state changed concurrently; reload before retrying",
        )
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let title = self
            .status
            .canonical_reason()
            .unwrap_or("Request failed")
            .to_owned();
        let body = Problem {
            problem_type: format!("https://razorproof.dev/problems/{}", self.code),
            title,
            status: self.status.as_u16(),
            code: self.code,
            detail: self.detail,
        };
        (
            self.status,
            [(header::CONTENT_TYPE, "application/problem+json")],
            Json(body),
        )
            .into_response()
    }
}

#[derive(Debug, thiserror::Error)]
pub enum ServerError {
    #[error("local authentication and webhook secrets do not meet the minimum length")]
    WeakLocalSecret,
    #[error(transparent)]
    Policy(#[from] razorproof_policy::PolicyError),
    #[error(transparent)]
    Provider(#[from] razorproof_provider::ProviderError),
    #[error(transparent)]
    Url(#[from] url::ParseError),
}

#[cfg(test)]
mod tests {
    use axum::{
        body::{Body, to_bytes},
        http::Request,
    };
    use hmac::{Hmac, Mac};
    use sha2::Sha256;
    use tower::ServiceExt;

    use super::*;

    async fn test_state() -> Result<(AppState, TenantId), Box<dyn std::error::Error>> {
        let catalog = Arc::new(OperationCatalog::embedded()?);
        let credentials = Credentials::new(
            "rzp_test_123456789",
            "test-secret-value-long-enough",
            NetworkMode::TestOnly,
        )?;
        let client = RazorpayClient::new(
            credentials,
            None,
            Url::parse("http://127.0.0.1:9/v1/")?,
            EndpointPolicy::AllowLoopback,
            Arc::clone(&catalog),
        )?;
        let tenant = TenantId::parse("merchant_test")?;
        Ok((
            AppState::with_client(
                Store::in_memory().await?,
                tenant.clone(),
                "gateway-token-with-enough-entropy".to_owned(),
                "webhook-secret-with-enough-entropy".to_owned(),
                client,
                catalog,
            ),
            tenant,
        ))
    }

    #[tokio::test]
    async fn quote_amount_is_server_computed_and_fractional_json_is_rejected()
    -> Result<(), Box<dyn std::error::Error>> {
        let (state, _) = test_state().await?;
        let app = router(state);
        let request = Request::builder()
            .method("POST")
            .uri("/v1/quotes")
            .header("content-type", "application/json")
            .header("x-razorproof-tenant", "merchant_test")
            .header("authorization", "Bearer gateway-token-with-enough-entropy")
            .body(Body::from(
                r#"{"currency":"INR","lines":[{"sku":"pro","unit_amount_minor":201,"quantity":2}]}"#,
            ))?;
        let response = app.clone().oneshot(request).await?;
        assert_eq!(response.status(), StatusCode::CREATED);
        let body = to_bytes(response.into_body(), 64 * 1024).await?;
        let value: Value = serde_json::from_slice(&body)?;
        assert_eq!(value["money"]["amount"], 402);

        let invalid = Request::builder()
            .method("POST")
            .uri("/v1/quotes")
            .header("content-type", "application/json")
            .header("x-razorproof-tenant", "merchant_test")
            .header("authorization", "Bearer gateway-token-with-enough-entropy")
            .body(Body::from(
                r#"{"currency":"INR","lines":[{"sku":"pro","unit_amount_minor":2.01,"quantity":1}]}"#,
            ))?;
        assert_eq!(
            app.oneshot(invalid).await?.status(),
            StatusCode::UNPROCESSABLE_ENTITY
        );
        Ok(())
    }

    #[tokio::test]
    async fn webhook_uses_raw_bytes_and_deduplicates_event_id()
    -> Result<(), Box<dyn std::error::Error>> {
        let (state, _) = test_state().await?;
        let app = router(state);
        let raw = br#"{"event":"payment.captured","note":"caf\u00e9"}"#;
        let mut mac = Hmac::<Sha256>::new_from_slice(b"webhook-secret-with-enough-entropy")?;
        mac.update(raw);
        let signature = hex::encode(mac.finalize().into_bytes());
        for duplicate in [false, true] {
            let request = Request::builder()
                .method("POST")
                .uri("/v1/webhooks/razorpay/merchant_test")
                .header("content-type", "application/json")
                .header("x-razorpay-event-id", "event_1")
                .header("x-razorpay-signature", &signature)
                .body(Body::from(raw.as_slice()))?;
            let response = app.clone().oneshot(request).await?;
            assert_eq!(response.status(), StatusCode::OK);
            let bytes = to_bytes(response.into_body(), 64 * 1024).await?;
            let value: Value = serde_json::from_slice(&bytes)?;
            assert_eq!(value["duplicate"], duplicate);
        }
        Ok(())
    }

    #[tokio::test]
    async fn dashboard_is_same_origin_and_not_frameable() -> Result<(), Box<dyn std::error::Error>>
    {
        let (state, _) = test_state().await?;
        let response = router(state)
            .oneshot(Request::builder().uri("/").body(Body::empty())?)
            .await?;
        assert_eq!(response.status(), StatusCode::OK);
        assert_eq!(response.headers()["x-frame-options"], "DENY");
        assert_eq!(response.headers()["x-content-type-options"], "nosniff");
        assert!(
            response.headers()["content-security-policy"]
                .to_str()?
                .contains("frame-ancestors 'none'")
        );
        Ok(())
    }
}
