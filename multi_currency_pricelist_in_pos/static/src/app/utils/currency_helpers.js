/** @odoo-module **/
import { roundPrecision as round_pr } from "@web/core/utils/numbers";

/**
 * Checks whether the Multi-Currency Pricelist feature is enabled in the POS.
 *
 * The feature is considered enabled only when both pricelists and
 * multi-currency pricelists are activated in the POS configuration.
 *
 * @param {Object} pos - The POS store instance.
 * @returns {boolean} `true` if multi-currency pricelists are enabled; otherwise `false`.
 */

export function isMultiCurrencyPricelistEnabled(pos) {
    return Boolean(pos?.config?.use_pricelist && pos?.config?.enable_multi_currency_pricelist);
}

export function getBaseCurrency(pos) {
    return pos?.currency || null;
}

export function getPricelistCurrency(pos, pricelist = null) {
    const baseCurrency = getBaseCurrency(pos);
    if (!isMultiCurrencyPricelistEnabled(pos)) {
        return baseCurrency;
    }
    const targetPricelist = pricelist || pos?.get_order()?.pricelist;
    const currencyId = targetPricelist?.currency_id?.[0] || targetPricelist?.currency_id;
    if (!currencyId) {
        return baseCurrency;
    }
    return pos?.getCurrencyById?.(currencyId) || baseCurrency;
}

export function getOrderCurrency(order) {
    return order?.pos ? getPricelistCurrency(order.pos, order.pricelist) : null;
}

export function getCurrencyRounding(orderOrPos, pricelist = null) {
    const currency = orderOrPos?.pos
        ? getOrderCurrency(orderOrPos)
        : getPricelistCurrency(orderOrPos, pricelist);
    return currency?.rounding || 0.01;
}

export function convertAmount(pos, amount, fromCurrency, toCurrency) {
    if (!fromCurrency || !toCurrency || !amount || fromCurrency.id === toCurrency.id) {
        return amount;
    }
    if (!fromCurrency.rate || !toCurrency.rate) {
        return amount;
    }
    return (amount / fromCurrency.rate) * toCurrency.rate;
}

export function convertOrderAmountToBaseCurrency(order, amount, shouldRound = true) {
    const baseCurrency = getBaseCurrency(order?.pos);
    const orderCurrency = getOrderCurrency(order);
    const convertedAmount = convertAmount(order?.pos, amount, orderCurrency, baseCurrency);
    if (!shouldRound || !baseCurrency) {
        return convertedAmount;
    }
    return round_pr(convertedAmount, baseCurrency.rounding);
}
