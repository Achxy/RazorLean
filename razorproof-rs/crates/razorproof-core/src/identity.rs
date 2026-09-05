// Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
// SPDX-License-Identifier: MIT
// Licensed under the MIT License. See LICENSE in the repository root.

use std::{fmt, str::FromStr};

use serde::{Deserialize, Serialize};
use thiserror::Error;
use uuid::Uuid;

#[derive(Debug, Error)]
pub enum IdentityError {
    #[error("identifier must contain 1 to 96 ASCII letters, digits, underscores, hyphens, or dots")]
    Invalid,
}

fn validate(value: &str) -> Result<(), IdentityError> {
    if value.is_empty()
        || value.len() > 96
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.'))
    {
        return Err(IdentityError::Invalid);
    }
    Ok(())
}

macro_rules! identifier {
    ($name:ident, $prefix:literal) => {
        #[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize, Deserialize)]
        #[serde(try_from = "String", into = "String")]
        pub struct $name(String);

        impl $name {
            pub fn new() -> Self {
                Self(format!("{}_{}", $prefix, Uuid::now_v7().simple()))
            }

            pub fn parse(value: impl Into<String>) -> Result<Self, IdentityError> {
                let value = value.into();
                validate(&value)?;
                Ok(Self(value))
            }

            pub fn as_str(&self) -> &str {
                &self.0
            }
        }

        impl Default for $name {
            fn default() -> Self {
                Self::new()
            }
        }

        impl TryFrom<String> for $name {
            type Error = IdentityError;

            fn try_from(value: String) -> Result<Self, Self::Error> {
                Self::parse(value)
            }
        }

        impl From<$name> for String {
            fn from(value: $name) -> Self {
                value.0
            }
        }

        impl FromStr for $name {
            type Err = IdentityError;

            fn from_str(value: &str) -> Result<Self, Self::Err> {
                Self::parse(value)
            }
        }

        impl fmt::Display for $name {
            fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
                formatter.write_str(&self.0)
            }
        }
    };
}

identifier!(TenantId, "tenant");
identifier!(QuoteId, "quote");
identifier!(IntentId, "intent");

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_path_and_header_metacharacters() {
        assert!(TenantId::parse("../../root").is_err());
        assert!(TenantId::parse("a\nb").is_err());
        assert!(TenantId::parse("tenant_safe-1.example").is_ok());
    }
}
