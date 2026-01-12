/**
 * Currency utilities for Costa Rica storage platform.
 * Handles CRC, USD, and EUR with proper formatting.
 */

import type { SupportedCurrency } from '@/types';

// Currency symbols
const CURRENCY_SYMBOLS: Record<SupportedCurrency, string> = {
  CRC: '₡',
  USD: '$',
  EUR: '€',
};

// Currency names (Spanish)
const CURRENCY_NAMES_ES: Record<SupportedCurrency, string> = {
  CRC: 'Colones',
  USD: 'Dólares',
  EUR: 'Euros',
};

// Currency names (English)
const CURRENCY_NAMES_EN: Record<SupportedCurrency, string> = {
  CRC: 'Colones',
  USD: 'Dollars',
  EUR: 'Euros',
};

/**
 * Format a number as currency with proper locale formatting.
 */
export function formatCurrency(
  amount: number,
  currency: SupportedCurrency = 'CRC',
  locale: 'es' | 'en' = 'es'
): string {
  const symbol = CURRENCY_SYMBOLS[currency];

  // Use Intl.NumberFormat for proper locale-specific formatting
  const formatter = new Intl.NumberFormat(locale === 'es' ? 'es-CR' : 'en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  return `${symbol}${formatter.format(amount)}`;
}

/**
 * Format currency with full currency code (e.g., "₡1,234.56 CRC")
 */
export function formatCurrencyWithCode(
  amount: number,
  currency: SupportedCurrency = 'CRC',
  locale: 'es' | 'en' = 'es'
): string {
  return `${formatCurrency(amount, currency, locale)} ${currency}`;
}

/**
 * Format a large number in a compact form (e.g., "₡1.2M")
 */
export function formatCurrencyCompact(
  amount: number,
  currency: SupportedCurrency = 'CRC',
  locale: 'es' | 'en' = 'es'
): string {
  const symbol = CURRENCY_SYMBOLS[currency];

  const formatter = new Intl.NumberFormat(locale === 'es' ? 'es-CR' : 'en-US', {
    notation: 'compact',
    compactDisplay: 'short',
    maximumFractionDigits: 1,
  });

  return `${symbol}${formatter.format(amount)}`;
}

/**
 * Get the currency symbol for a currency code.
 */
export function getCurrencySymbol(currency: SupportedCurrency): string {
  return CURRENCY_SYMBOLS[currency] || currency;
}

/**
 * Get the currency name in the specified locale.
 */
export function getCurrencyName(
  currency: SupportedCurrency,
  locale: 'es' | 'en' = 'es'
): string {
  const names = locale === 'es' ? CURRENCY_NAMES_ES : CURRENCY_NAMES_EN;
  return names[currency] || currency;
}

/**
 * Parse a formatted currency string back to a number.
 */
export function parseCurrency(value: string): number {
  // Remove currency symbols and formatting
  const cleaned = value
    .replace(/[₡$€]/g, '')
    .replace(/\s/g, '')
    .replace(/,/g, '');

  return parseFloat(cleaned) || 0;
}

/**
 * Convert amount between currencies using a given rate.
 */
export function convertAmount(
  amount: number,
  rate: number,
  direction: 'multiply' | 'divide' = 'multiply'
): number {
  if (direction === 'multiply') {
    return Math.round(amount * rate * 100) / 100;
  }
  return Math.round((amount / rate) * 100) / 100;
}

/**
 * Format an amount with dual currency display.
 * Example: "₡65,000 (~$100 USD)"
 */
export function formatDualCurrency(
  primaryAmount: number,
  primaryCurrency: SupportedCurrency,
  secondaryAmount: number,
  secondaryCurrency: SupportedCurrency,
  locale: 'es' | 'en' = 'es'
): string {
  const primary = formatCurrency(primaryAmount, primaryCurrency, locale);
  const secondary = formatCurrency(secondaryAmount, secondaryCurrency, locale);
  return `${primary} (~${secondary} ${secondaryCurrency})`;
}

/**
 * Validate if a string is a valid currency code.
 */
export function isValidCurrency(code: string): code is SupportedCurrency {
  return ['CRC', 'USD', 'EUR'].includes(code);
}

/**
 * Get all supported currencies with their details.
 */
export function getSupportedCurrencies(locale: 'es' | 'en' = 'es') {
  const currencies: SupportedCurrency[] = ['CRC', 'USD', 'EUR'];

  return currencies.map((code) => ({
    code,
    symbol: getCurrencySymbol(code),
    name: getCurrencyName(code, locale),
  }));
}

/**
 * Default exchange rates (fallback when API is unavailable).
 * These should be updated periodically.
 */
export const DEFAULT_RATES = {
  USD_TO_CRC: 520,
  EUR_TO_CRC: 560,
};

/**
 * Calculate approximate CRC amount from USD.
 */
export function usdToCrc(usdAmount: number, rate?: number): number {
  return convertAmount(usdAmount, rate || DEFAULT_RATES.USD_TO_CRC, 'multiply');
}

/**
 * Calculate approximate USD amount from CRC.
 */
export function crcToUsd(crcAmount: number, rate?: number): number {
  return convertAmount(crcAmount, rate || DEFAULT_RATES.USD_TO_CRC, 'divide');
}
