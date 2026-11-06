import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";

/**
 * Patch to extend the ProductScreen and conditionally disable
 * numpad-related buttons based on cashier permissions.
 */
patch(ProductScreen.prototype, {
    /**
     * Patch to extend the ProductScreen and conditionally disable
     * numpad-related buttons based on cashier permissions.
     */
    getNumpadButtons() {
        const buttons = super.getNumpadButtons(...arguments);
        const cashier = this.pos && this.pos.getCashier ? this.pos.getCashier() : null;
        if (!cashier) {
            return buttons;
        }

        return buttons.map((button) => {
            let customDisabled = false;
            switch(button.value) {
                case "1": case "2": case "3": case "4": case "5":
                case "6": case "7": case "8": case "9": case "0":
                case this.env.services.localization.decimalPoint:
                    customDisabled = !!cashier.disable_numpad;
                    break;
                case "quantity":
                    customDisabled = !!cashier.disable_qty;
                    break;
                case "discount":
                    customDisabled = !!cashier.disable_discount;
                    break;
                case "price":
                    customDisabled = !!cashier.disable_price;
                    break;
                case "-":
                    customDisabled = !!cashier.disable_plus_minus;
                    break;
                case "Backspace":
                    customDisabled = !!cashier.disable_remove_button;
                    break;
            }

            return {
                ...button,
                disabled: button.disabled || customDisabled,
            };
        });
    }
});
