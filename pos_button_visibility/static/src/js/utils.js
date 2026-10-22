/** @odoo-module */

/**
 * Resolves the active cashier (user or pos_hr employee) in the Point of Sale.
 *
 * @param {Object} pos - POS store instance
 * @returns {Object|null} Active cashier record
 */
export function getCashier(pos) {
    return pos?.accessRight?.loggedCashier || null;
}

/**
 * Checks if a specific POS button is restricted for the current cashier and POS config.
 *
 * @param {Object} pos - POS store instance
 * @param {string} buttonName - Name of the button to check (e.g. "Discount", "Price", "Reward", "Refund")
 * @returns {boolean} True if restricted, false otherwise
 */
export function isButtonRestricted(pos, buttonName) {
    if (!pos) {
        return false;
    }
    const cashier = getCashier(pos);
    if (!cashier) {
        return false;
    }

    // Check POS configurations restriction (empty pos_config_ids means restriction applies to all POS configs)
    const configIds = cashier.pos_config_ids || [];
    if (configIds.length > 0) {
        const ids = configIds.map((c) => (typeof c === "object" && c !== null ? c.id : c));
        if (pos.config?.id && !ids.includes(pos.config.id)) {
            return false;
        }
    }

    // Check button restrictions
    const buttons = cashier.pos_button_ids || [];
    for (const b of buttons) {
        const btnRec = typeof b === "object" && b !== null ? b : pos.models?.["pos.button"]?.get(b);
        const name = btnRec?.name || (typeof b === "string" ? b : null);
        if (name === buttonName) {
            return true;
        }
    }
    return false;
}
