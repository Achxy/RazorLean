// Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
// SPDX-License-Identifier: MIT
// Licensed under the MIT License. See LICENSE in the repository root.

use std::{fmt, str::FromStr};

use rust_decimal::{Decimal, prelude::ToPrimitive};
use serde::{Deserialize, Serialize};
use thiserror::Error;

const MAX_SAFE_JSON_INTEGER: i64 = 9_007_199_254_740_991;

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct CurrencyRule {
    pub exponent: u8,
    pub minor_quantum: u32,
}

impl CurrencyRule {
    #[must_use]
    pub const fn new(exponent: u8, minor_quantum: u32) -> Self {
        Self {
            exponent,
            minor_quantum,
        }
    }
}

#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize, Deserialize)]
#[serde(try_from = "String", into = "String")]
pub struct Currency(String);

impl Currency {
    pub fn parse(value: impl AsRef<str>) -> Result<Self, MoneyError> {
        let value = value.as_ref();
        if value.len() != 3 || !value.bytes().all(|byte| byte.is_ascii_uppercase()) {
            return Err(MoneyError::InvalidCurrency(value.to_owned()));
        }
        Ok(Self(value.to_owned()))
    }

    #[must_use]
    pub fn code(&self) -> &str {
        &self.0
    }

    #[must_use]
    pub fn rule(&self) -> CurrencyRule {
        match self.0.as_str() {
            "JPY" => CurrencyRule::new(0, 1),
            "BHD" | "KWD" | "OMR" => CurrencyRule::new(3, 10),
            _ => CurrencyRule::new(2, 1),
        }
    }
}

impl TryFrom<String> for Currency {
    type Error = MoneyError;

    fn try_from(value: String) -> Result<Self, Self::Error> {
        Self::parse(value)
    }
}

impl From<Currency> for String {
    fn from(value: Currency) -> Self {
        value.0
    }
}

impl fmt::Display for Currency {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.0)
    }
}

impl FromStr for Currency {
    type Err = MoneyError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        Self::parse(value)
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize, Deserialize)]
#[serde(try_from = "i64", into = "i64")]
pub struct MinorAmount(i64);

impl MinorAmount {
    pub fn new(value: i64) -> Result<Self, MoneyError> {
        if value <= 0 {
            return Err(MoneyError::NonPositive(value));
        }
        if value > MAX_SAFE_JSON_INTEGER {
            return Err(MoneyError::UnsafeJsonInteger(value));
        }
        Ok(Self(value))
    }

    #[must_use]
    pub const fn get(self) -> i64 {
        self.0
    }

    pub fn checked_mul(self, multiplier: u32) -> Result<Self, MoneyError> {
        let multiplier = i64::from(multiplier);
        let value = self.0.checked_mul(multiplier).ok_or(MoneyError::Overflow)?;
        Self::new(value)
    }

    pub fn checked_add(self, other: Self) -> Result<Self, MoneyError> {
        let value = self.0.checked_add(other.0).ok_or(MoneyError::Overflow)?;
        Self::new(value)
    }
}

impl TryFrom<i64> for MinorAmount {
    type Error = MoneyError;

    fn try_from(value: i64) -> Result<Self, Self::Error> {
        Self::new(value)
    }
}

impl From<MinorAmount> for i64 {
    fn from(value: MinorAmount) -> Self {
        value.0
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct Money {
    pub amount: MinorAmount,
    pub currency: Currency,
}

impl Money {
    pub fn from_minor(amount: i64, currency: Currency) -> Result<Self, MoneyError> {
        let amount = MinorAmount::new(amount)?;
        let rule = currency.rule();
        if amount.get() % i64::from(rule.minor_quantum) != 0 {
            return Err(MoneyError::UnsupportedQuantum {
                currency: currency.to_string(),
                quantum: rule.minor_quantum,
                amount: amount.get(),
            });
        }
        Ok(Self { amount, currency })
    }

    pub fn from_major(value: &str, currency: Currency) -> Result<Self, MoneyError> {
        let decimal = Decimal::from_str_exact(value)
            .map_err(|_| MoneyError::InvalidDecimal(value.to_owned()))?;
        if decimal <= Decimal::ZERO {
            return Err(MoneyError::InvalidDecimal(value.to_owned()));
        }
        let rule = currency.rule();
        let factor = Decimal::from(10_u64.pow(u32::from(rule.exponent)));
        let minor = decimal.checked_mul(factor).ok_or(MoneyError::Overflow)?;
        if !minor.fract().is_zero() {
            return Err(MoneyError::ExcessPrecision {
                currency: currency.to_string(),
                exponent: rule.exponent,
                value: value.to_owned(),
            });
        }
        let minor = minor.to_i64().ok_or(MoneyError::Overflow)?;
        Self::from_minor(minor, currency)
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum MoneyError {
    #[error("invalid three-letter uppercase currency code: {0}")]
    InvalidCurrency(String),
    #[error("amount must be positive, got {0}")]
    NonPositive(i64),
    #[error("amount exceeds the exact JSON integer range: {0}")]
    UnsafeJsonInteger(i64),
    #[error("invalid exact decimal amount: {0}")]
    InvalidDecimal(String),
    #[error("{value} has more precision than {currency} permits ({exponent} decimal places)")]
    ExcessPrecision {
        currency: String,
        exponent: u8,
        value: String,
    },
    #[error("{currency} amount {amount} must be a multiple of minor-unit quantum {quantum}")]
    UnsupportedQuantum {
        currency: String,
        quantum: u32,
        amount: i64,
    },
    #[error("money arithmetic overflow")]
    Overflow,
}

#[cfg(test)]
mod tests {
    use super::*;

    fn currency(code: &str) -> Result<Currency, MoneyError> {
        Currency::parse(code)
    }

    #[test]
    fn converts_known_currency_exponents_exactly() -> Result<(), MoneyError> {
        assert_eq!(
            Money::from_major("2.01", currency("INR")?)?.amount.get(),
            201
        );
        assert_eq!(
            Money::from_major("295", currency("JPY")?)?.amount.get(),
            295
        );
        assert_eq!(
            Money::from_major("295.990", currency("KWD")?)?.amount.get(),
            295_990
        );
        Ok(())
    }

    #[test]
    fn rejects_float_style_precision_and_three_decimal_quantum() -> Result<(), MoneyError> {
        assert!(Money::from_major("2.001", currency("INR")?).is_err());
        assert!(Money::from_major("295.991", currency("KWD")?).is_err());
        assert!(Money::from_minor(295_991, currency("KWD")?).is_err());
        Ok(())
    }
}
