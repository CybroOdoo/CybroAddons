/** @odoo-module **/

import {
    formatFloat,
    roundDecimals,
    floatIsZero as genericFloatIsZero,
} from "@web/core/utils/numbers";
import { escapeRegExp } from "@web/core/utils/strings";
import { parseFloat } from "@web/views/fields/parsers";
import { patch } from "@web/core/utils/patch";
import { contextualUtilsService } from "@point_of_sale/app/utils/contextual_utils_service";
import { getPricelistCurrency } from "@pos_multi_currency_pricelist/app/utils/currency_helpers";

function normalizeCurrencyArgs(hasSymbolOrCurrency, currencyArg) {
    if (typeof hasSymbolOrCurrency === "object" && hasSymbolOrCurrency?.id) {
        return {
            hasSymbol: true,
            currency: hasSymbolOrCurrency,
        };
    }
    return {
        hasSymbol: hasSymbolOrCurrency ?? true,
        currency: currencyArg,
    };
}

function toNumericValue(value) {
    if (value === false || value === null || value === undefined || value === "") {
        return null;
    }
    if (typeof value === "number") {
        return Number.isFinite(value) ? value : null;
    }
    if (typeof value === "string") {
        const parsedValue = parseFloat(value);
        return Number.isFinite(parsedValue) ? parsedValue : null;
    }
    const parsedValue = Number(value);
    return Number.isFinite(parsedValue) ? parsedValue : null;
}

function formatWithSymbol(value, currency, hasSymbol) {
    const numericValue = toNumericValue(value);
    if (numericValue === null) {
        return "";
    }
    const formattedValue = formatFloat(numericValue, {
        digits: [69, currency.decimal_places ?? 2],
    });
    if (!hasSymbol || !currency?.symbol) {
        return formattedValue;
    }
    return currency.position === "after"
        ? `${formattedValue} ${currency.symbol}`
        : `${currency.symbol} ${formattedValue}`;
}

patch(contextualUtilsService, {
    start(env, { pos, localization }) {
        const result = super.start(...arguments);
        const decimalPoint = localization.decimalPoint;
        const thousandsSep = localization.thousandsSep;
        const escapedDecimalPoint = escapeRegExp(decimalPoint);
        let floatRegex;
        if (thousandsSep) {
            const escapedThousandsSep = escapeRegExp(thousandsSep);
            floatRegex = new RegExp(
                `^-?(?:\\d+(${escapedThousandsSep}\\d+)*)?(?:${escapedDecimalPoint}\\d*)?$`
            );
        } else {
            floatRegex = new RegExp(`^-?(?:\\d+)?(?:${escapedDecimalPoint}\\d*)?$`);
        }

        env.utils.formatCurrency = (value, hasSymbolOrCurrency = true, currencyArg = null) => {
            const { hasSymbol, currency } = normalizeCurrencyArgs(
                hasSymbolOrCurrency,
                currencyArg
            );
            return formatWithSymbol(value, currency || getPricelistCurrency(pos), hasSymbol);
        };
        env.utils.formatStrCurrency = (
            valueStr,
            hasSymbolOrCurrency = true,
            currencyArg = null
        ) => env.utils.formatCurrency(parseFloat(valueStr), hasSymbolOrCurrency, currencyArg);
        env.utils.floatIsZero = (value, currency = null) =>
            genericFloatIsZero(
                toNumericValue(value) || 0,
                (currency || getPricelistCurrency(pos)).decimal_places
            );
        env.utils.roundCurrency = (value, currency = null) =>
            roundDecimals(
                toNumericValue(value) || 0,
                (currency || getPricelistCurrency(pos)).decimal_places
            );
        env.utils.isValidFloat = (inputValue) =>
            ![decimalPoint, "-"].includes(inputValue) && floatRegex.test(inputValue);
        return result;
    },
});
