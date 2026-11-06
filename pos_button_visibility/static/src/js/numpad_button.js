/** @odoo-module */

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";

const NUMPAD_BUTTONS = {
    discount: "Discount",
    price: "Price",
};

/**
 * Return the names of the POS buttons restricted for the active cashier.
 * Evaluated on every call so that a cashier change is picked up at once.
 * With pos_hr the cashier is an hr.employee, so the restrictions of the
 * logged-in user are used instead.
 */
export function getRestrictedPosButtons(pos) {
    const cashier = pos.get_cashier();
    const user =
        cashier?.model?.modelName === "res.users" ? cashier : pos.user;
    return new Set(
        (user?.buttons_pos_ids || []).map((button) => button.name)
    );
}

function isNumpadButtonRestricted(pos, buttonValue) {
    const buttonName = NUMPAD_BUTTONS[buttonValue];
    return Boolean(buttonName) && getRestrictedPosButtons(pos).has(buttonName);
}

patch(ProductScreen.prototype, {
    getNumpadButtons() {
        return super.getNumpadButtons(...arguments).map((button) =>
            isNumpadButtonRestricted(this.pos, button.value)
                ? { ...button, disabled: true }
                : button
        );
    },

    onNumpadClick(buttonValue) {
        if (isNumpadButtonRestricted(this.pos, buttonValue)) {
            return;
        }
        return super.onNumpadClick(...arguments);
    },
});
