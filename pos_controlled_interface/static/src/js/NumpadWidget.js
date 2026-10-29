/** @odoo-module */

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";

patch(ProductScreen.prototype, {
    getNumpadButtons() {
        const buttons = super.getNumpadButtons();
        const isControlDiscountEnabled = Boolean(this.pos?.config?.control_discount);

        for (const button of buttons) {
            if (button.value === "discount" && isControlDiscountEnabled) {
                button.disabled = true;
            }
        }
        return buttons;
    },
});
