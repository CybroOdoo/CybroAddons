/** @odoo-module **/

import { roundPrecision as round_pr } from "@web/core/utils/numbers";

function getConfig(source) {
    return source?.config || source?.models?.["pos.config"]?.getFirst?.() || null;
}

function getCurrentPricelist(source) {
    if (source?.pricelist_id) {
        return source.pricelist_id;
    }
    return source?.get_order?.()?.pricelist_id || null;
}

function getCurrencyRecord(source, currencyRef) {
    if (!currencyRef) {
        return null;
    }
    if (typeof currencyRef === "object" && "id" in currencyRef) {
        return currencyRef;
    }
    const currencyId = Array.isArray(currencyRef) ? currencyRef[0] : currencyRef;
    const models = source?.models || source?.data?.models;
    return models?.["res.currency"]?.get?.(currencyId) || null;
}

export function isMultiCurrencyPricelistEnabled(source) {
    const config = getConfig(source);
    return Boolean(config?.use_pricelist && config?.enable_multi_currency_pricelist);
}

export function getBaseCurrency(source) {
    return getConfig(source)?.currency_id || source?.currency || null;
}

export function getPricelistCurrency(source, pricelist = null) {
    const baseCurrency = getBaseCurrency(source);
    if (!isMultiCurrencyPricelistEnabled(source)) {
        return baseCurrency;
    }
    const targetPricelist = pricelist || getCurrentPricelist(source);
    if (!targetPricelist?.currency_id) {
        return baseCurrency;
    }
    return getCurrencyRecord(source, targetPricelist.currency_id) || baseCurrency;
}

export function getOrderCurrency(order) {
    return order ? getPricelistCurrency(order, order.pricelist_id) : null;
}

export function getCurrencyRounding(source, pricelist = null) {
    const currency = source?.pricelist_id
        ? getOrderCurrency(source)
        : getPricelistCurrency(source, pricelist);
    return currency?.rounding || 0.01;
}

export function getCurrencyDecimalPlaces(source, pricelist = null) {
    const currency = source?.pricelist_id
        ? getOrderCurrency(source)
        : getPricelistCurrency(source, pricelist);
    return currency?.decimal_places ?? 2;
}

export function convertAmount(amount, fromCurrency, toCurrency) {
    if (!fromCurrency || !toCurrency || !amount || fromCurrency.id === toCurrency.id) {
        return amount;
    }
    if (!fromCurrency.rate || !toCurrency.rate) {
        return amount;
    }
    return (amount / fromCurrency.rate) * toCurrency.rate;
}

export function convertOrderAmountToBaseCurrency(order, amount, shouldRound = true) {
    const baseCurrency = getBaseCurrency(order);
    const orderCurrency = getOrderCurrency(order);
    const convertedAmount = convertAmount(amount, orderCurrency, baseCurrency);
    if (!shouldRound || !baseCurrency) {
        return convertedAmount;
    }
    return round_pr(convertedAmount, baseCurrency.rounding);
}
