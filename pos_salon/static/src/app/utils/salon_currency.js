export function formatSalonAmount(pos, value) {
    const currency = pos.currency || pos.config.currency_id || {};
    const decimals = currency.decimal_places ?? 2;
    const number = Number(value || 0).toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    });
    const symbol = currency.symbol || "";
    return currency.position === "before" ? `${symbol}${number}` : `${number} ${symbol}`;
}
