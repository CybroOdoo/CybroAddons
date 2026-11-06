/** @odoo-module **/

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";

/**
 * Patch to extend the ProductScreen and conditionally disable
 * numpad-related buttons based on cashier permissions.
 */
patch(ProductScreen.prototype, {
    /**
     * Returns the configuration of numpad buttons for the POS interface.
     * Each button's disabled state is determined by the cashier's permissions.
     *
     * @returns {Array<Object>} List of button configurations with optional disabled states and CSS classes.
     */
    getNumpadButtons() {
        return [
            { value: "1", disabled: this.pos.cashier?.disable_numpad },
            { value: "2", disabled: this.pos.cashier?.disable_numpad },
            { value: "3", disabled: this.pos.cashier?.disable_numpad },
            { value: "quantity", text: "Qty", disabled: this.pos.cashier?.disable_qty },
            { value: "4", disabled: this.pos.cashier?.disable_numpad },
            { value: "5", disabled: this.pos.cashier?.disable_numpad },
            { value: "6", disabled: this.pos.cashier?.disable_numpad },
            {
                value: "discount",
                text: "% Disc",
                disabled: !this.pos.config?.manual_discount || this.pos.cashier?.disable_discount,
            },
            { value: "7", disabled: this.pos.cashier?.disable_numpad },
            { value: "8", disabled: this.pos.cashier?.disable_numpad },
            { value: "9", disabled: this.pos.cashier?.disable_numpad },
            {
                value: "price",
                text: "Price",
                disabled: !this.pos.cashierHasPriceControlRights() || this.pos.cashier?.disable_price,
            },
            { value: "-", text: "+/-", disabled: this.pos.cashier?.disable_plus_minus },
            { value: "0", disabled: this.pos.cashier?.disable_numpad },
            { value: this.env.services.localization.decimalPoint, disabled: this.pos.cashier?.disable_numpad },
            { value: "Backspace", text: "⌫", disabled: this.pos.cashier?.disable_remove_button },
        ].map((button) => ({
            ...button,
            class: this.pos.numpadMode === button.value ? "active border-primary" : "",
        }));
    }
});
