#![doc = "`RazorProof` command-line control plane."]
// Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
// SPDX-License-Identifier: MIT
// Licensed under the MIT License. See LICENSE in the repository root.

use std::{
    collections::BTreeMap,
    fs,
    net::SocketAddr,
    path::{Path, PathBuf},
    sync::Arc,
};

use anyhow::{Context, Result, anyhow, bail};
use clap::{Args, Parser, Subcommand};
use razorproof_core::{Currency, Money, TenantId, verify_evidence_chain};
use razorproof_engine::scan_repositories;
use razorproof_policy::OperationCatalog;
use razorproof_provider::{Credentials, EndpointPolicy, NetworkMode, RazorpayClient};
use razorproof_server::{AppState, TenantConfig, router};
use razorproof_store::Store;
use serde_json::{Value, json};
use tracing_subscriber::EnvFilter;
use url::Url;

#[derive(Debug, Parser)]
#[command(
    name = "razorproof",
    version,
    about = "Semantic payment firewall and conformance compiler"
)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Subcommand)]
enum Command {
    /// Print the versioned operation policy catalog.
    Catalog,
    /// Prove the embedded catalog covers the current Razorpay MCP source.
    Coverage {
        #[arg(long)]
        source: PathBuf,
    },
    /// Scan official SDK and generator source trees for semantic defects.
    Scan {
        #[arg(long)]
        repositories: PathBuf,
        #[arg(long, default_value = "artifacts/conformance")]
        output: PathBuf,
    },
    /// Exercise exact-money, catalog, and evidence invariants without a network.
    SelfTest,
    /// Make one read-only call to Razorpay Test Mode and print redacted evidence.
    ProbeTestMode {
        #[command(flatten)]
        credentials: CredentialOptions,
    },
    /// Run the authenticated Test Mode firewall and judge dashboard.
    Serve {
        #[command(flatten)]
        credentials: CredentialOptions,
        #[arg(long, env = "RAZORPROOF_TENANT", default_value = "hackathon_demo")]
        tenant: String,
        #[arg(long, env = "RAZORPROOF_GATEWAY_TOKEN")]
        gateway_token: String,
        #[arg(long, env = "RAZORPROOF_WEBHOOK_SECRET")]
        webhook_secret: String,
        #[arg(long, env = "RAZORPROOF_PARTNER_ACCOUNT")]
        partner_account: Option<String>,
        #[arg(
            long,
            env = "RAZORPROOF_DATABASE_URL",
            default_value = "sqlite://razorproof.db"
        )]
        database_url: String,
        #[arg(long, env = "RAZORPROOF_BIND", default_value = "127.0.0.1:8787")]
        bind: SocketAddr,
    },
    /// Verify one tenant's persisted tamper-evident evidence chain.
    VerifyEvidence {
        #[arg(long)]
        database_url: String,
        #[arg(long)]
        tenant: String,
    },
}

#[derive(Debug, Args)]
struct CredentialOptions {
    /// Razorpay dashboard CSV export; safer than command-line secrets.
    #[arg(long, env = "RAZORPROOF_KEY_CSV")]
    key_csv: Option<PathBuf>,
    #[arg(long, env = "RAZORPAY_KEY_ID", hide_env_values = true)]
    key_id: Option<String>,
    #[arg(long, env = "RAZORPAY_KEY_SECRET", hide_env_values = true)]
    key_secret: Option<String>,
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info")),
        )
        .with_target(false)
        .compact()
        .init();
    let cli = Cli::parse();
    match cli.command {
        Command::Catalog => {
            let catalog = OperationCatalog::embedded()?;
            println!("{}", serde_json::to_string_pretty(&catalog)?);
        }
        Command::Coverage { source } => coverage(&source)?,
        Command::Scan {
            repositories,
            output,
        } => scan(&repositories, &output)?,
        Command::SelfTest => self_test()?,
        Command::ProbeTestMode { credentials } => probe_test_mode(&credentials).await?,
        Command::Serve {
            credentials,
            tenant,
            gateway_token,
            webhook_secret,
            partner_account,
            database_url,
            bind,
        } => {
            serve(
                &credentials,
                tenant,
                gateway_token,
                webhook_secret,
                partner_account,
                &database_url,
                bind,
            )
            .await?;
        }
        Command::VerifyEvidence {
            database_url,
            tenant,
        } => verify_evidence(&database_url, &tenant).await?,
    }
    Ok(())
}

fn coverage(source: &Path) -> Result<()> {
    let mut concatenated = String::new();
    collect_go_source(source, &mut concatenated)?;
    let catalog = OperationCatalog::embedded()?;
    let report = catalog.audit_mcp_source(&concatenated)?;
    println!("{}", serde_json::to_string_pretty(&report)?);
    if !report.complete {
        bail!("operation catalog drift detected; update the policy before shipping");
    }
    Ok(())
}

fn collect_go_source(path: &Path, output: &mut String) -> Result<()> {
    if path.is_file() {
        if is_production_go(path) {
            output.push_str(&fs::read_to_string(path)?);
            output.push('\n');
        }
        return Ok(());
    }
    for entry in fs::read_dir(path).with_context(|| format!("cannot read {}", path.display()))? {
        let path = entry?.path();
        if matches!(
            path.file_name().and_then(|value| value.to_str()),
            Some(".git" | "testdata")
        ) {
            continue;
        }
        if path.is_dir() {
            collect_go_source(&path, output)?;
        } else if is_production_go(&path) {
            output.push_str(&fs::read_to_string(&path)?);
            output.push('\n');
        }
    }
    Ok(())
}

fn is_production_go(path: &Path) -> bool {
    path.extension().and_then(|value| value.to_str()) == Some("go")
        && !path
            .file_name()
            .and_then(|value| value.to_str())
            .is_some_and(|name| name.ends_with("_test.go"))
}

fn scan(repositories: &Path, output: &Path) -> Result<()> {
    let report = scan_repositories(repositories)?;
    fs::create_dir_all(output)?;
    fs::write(
        output.join("scan.json"),
        format!("{}\n", serde_json::to_string_pretty(&report)?),
    )?;
    fs::write(output.join("scan.md"), report.to_markdown())?;
    println!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "files_scanned": report.files_scanned,
            "bytes_scanned": report.bytes_scanned,
            "detectors": report.detector_count,
            "findings": report.findings.len(),
            "direct_defects": report.direct_defects,
            "failure_chains": report.chains.len(),
            "output": output,
        }))?
    );
    Ok(())
}

fn self_test() -> Result<()> {
    let catalog = OperationCatalog::embedded()?;
    let controls = [
        ("INR", "2.01", 201_i64),
        ("JPY", "295", 295_i64),
        ("KWD", "295.990", 295_990_i64),
    ];
    let results = controls
        .into_iter()
        .map(|(currency, major, expected)| {
            let actual = Money::from_major(major, Currency::parse(currency)?)?
                .amount
                .get();
            if actual != expected {
                bail!("money invariant failed for {currency}");
            }
            Ok(json!({"currency": currency, "major": major, "minor": actual, "pass": true}))
        })
        .collect::<Result<Vec<_>>>()?;
    if catalog
        .validate_request("create_refund", &json!({"amount": 100.75}))
        .is_ok()
    {
        bail!("fractional refund crossed the policy boundary");
    }
    println!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "status": "pass",
            "catalog_operations": catalog.operations.len(),
            "exact_money_controls": results,
            "fractional_refund_rejected": true,
            "live_credentials_permitted": false
        }))?
    );
    Ok(())
}

async fn probe_test_mode(options: &CredentialOptions) -> Result<()> {
    let (key_id, key_secret) = load_credentials(options)?;
    let catalog = Arc::new(OperationCatalog::embedded()?);
    let credentials = Credentials::new(key_id, key_secret, NetworkMode::TestOnly)?;
    let key_fingerprint = credentials.key_fingerprint();
    let client = RazorpayClient::new(
        credentials,
        None,
        Url::parse("https://api.razorpay.com/v1/")?,
        EndpointPolicy::OfficialOnly,
        catalog,
    )?;
    let response = client
        .execute(
            "fetch_all_orders",
            &BTreeMap::new(),
            &BTreeMap::from([("count".to_owned(), vec!["1".to_owned()])]),
            &Value::Null,
            None,
        )
        .await?;
    println!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "mode": "test",
            "key_fingerprint": key_fingerprint,
            "status": response.status,
            "attempts": response.attempts,
            "request_id_fingerprint": response.request_id.as_ref().map(|value| blake3::hash(value.as_bytes()).to_hex()[..16].to_owned()),
            "response_shape": response_shape(&response.body)
        }))?
    );
    if !response.is_success() {
        bail!("Razorpay Test Mode read returned HTTP {}", response.status);
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
async fn serve(
    credentials: &CredentialOptions,
    tenant: String,
    gateway_token: String,
    webhook_secret: String,
    partner_account: Option<String>,
    database_url: &str,
    bind: SocketAddr,
) -> Result<()> {
    let (key_id, key_secret) = load_credentials(credentials)?;
    let tenant_id = TenantId::parse(tenant)?;
    let store = Store::connect(database_url).await?;
    let state = AppState::single_tenant(
        store,
        TenantConfig {
            tenant_id: tenant_id.clone(),
            gateway_token,
            webhook_secret,
            key_id,
            key_secret,
            partner_account,
        },
    )?;
    let listener = tokio::net::TcpListener::bind(bind).await?;
    tracing::info!(%bind, tenant = tenant_id.as_str(), mode = "test_only", "RazorProof listening");
    axum::serve(listener, router(state))
        .with_graceful_shutdown(shutdown_signal())
        .await?;
    Ok(())
}

async fn verify_evidence(database_url: &str, tenant: &str) -> Result<()> {
    let store = Store::connect(database_url).await?;
    let tenant = TenantId::parse(tenant)?;
    let mut events = store.list_evidence(&tenant, 500).await?;
    events.reverse();
    verify_evidence_chain(&events)?;
    println!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "status": "valid",
            "tenant": tenant,
            "events_verified": events.len(),
            "head": events.last().map(|event| &event.chain_hash)
        }))?
    );
    Ok(())
}

fn load_credentials(options: &CredentialOptions) -> Result<(String, String)> {
    match (&options.key_id, &options.key_secret, &options.key_csv) {
        (Some(key_id), Some(key_secret), _) => Ok((key_id.clone(), key_secret.clone())),
        (None, None, Some(path)) => parse_key_csv(path),
        (None, None, None) => Err(anyhow!(
            "provide --key-csv or both RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET"
        )),
        _ => Err(anyhow!("key id and key secret must be supplied together")),
    }
}

fn parse_key_csv(path: &Path) -> Result<(String, String)> {
    let contents = fs::read_to_string(path)
        .with_context(|| format!("cannot read credential CSV {}", path.display()))?;
    let mut rows = contents.lines().filter(|line| !line.trim().is_empty());
    let header = split_csv_row(
        rows.next()
            .ok_or_else(|| anyhow!("credential CSV is empty"))?,
    );
    let values = split_csv_row(
        rows.next()
            .ok_or_else(|| anyhow!("credential CSV has no value row"))?,
    );
    let normalized = header
        .iter()
        .map(|value| value.to_ascii_lowercase().replace([' ', '_', '-'], ""))
        .collect::<Vec<_>>();
    let key_index = normalized
        .iter()
        .position(|value| matches!(value.as_str(), "keyid" | "key"))
        .ok_or_else(|| anyhow!("credential CSV has no Key Id column"))?;
    let secret_index = normalized
        .iter()
        .position(|value| matches!(value.as_str(), "keysecret" | "secret"))
        .ok_or_else(|| anyhow!("credential CSV has no Key Secret column"))?;
    let key_id = values
        .get(key_index)
        .filter(|value| !value.is_empty())
        .ok_or_else(|| anyhow!("credential CSV Key Id is empty"))?;
    let key_secret = values
        .get(secret_index)
        .filter(|value| !value.is_empty())
        .ok_or_else(|| anyhow!("credential CSV Key Secret is empty"))?;
    Ok((key_id.clone(), key_secret.clone()))
}

fn split_csv_row(row: &str) -> Vec<String> {
    row.split(',')
        .map(|value| value.trim().trim_matches('"').to_owned())
        .collect()
}

fn response_shape(value: &Value) -> Value {
    match value {
        Value::Object(map) => json!({
            "type": "object",
            "keys": map.keys().cloned().collect::<Vec<_>>()
        }),
        Value::Array(values) => json!({"type": "array", "length": values.len()}),
        Value::Null => json!({"type": "null"}),
        _ => json!({"type": "scalar"}),
    }
}

async fn shutdown_signal() {
    let interrupt = async {
        let _ = tokio::signal::ctrl_c().await;
    };
    #[cfg(unix)]
    let terminate = async {
        if let Ok(mut signal) =
            tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
        {
            signal.recv().await;
        }
    };
    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();
    tokio::select! {
        () = interrupt => {},
        () = terminate => {},
    }
}
