/** @odoo-module */
/**
 * Patch: ProductScreen, PosStore, and PosAccessRightPlugin (POS)
 *
 * Overrides getNumpadButtons, onNumpadClick, setDiscountFromUI, and access rights
 * to dynamically disable and restrict Discount and Price options based on cashier configuration and POS configuration.
 */
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { PosAccessRightPlugin } from "@point_of_sale/app/plugins/access_right_plugin";
import { patch } from "@web/core/utils/patch";
import { isButtonRestricted } from "@pos_button_visibility/js/utils";

patch(ProductScreen.prototype, {
    get isDiscountRestricted() {
        return isButtonRestricted(this.pos, "Discount");
    },
    get isPriceRestricted() {
        return isButtonRestricted(this.pos, "Price");
    },
    getNumpadButtons() {
        if (this.isDiscountRestricted && this.pos.numpadMode === "discount") {
            this.pos.numpadMode = "quantity";
        }
        if (this.isPriceRestricted && this.pos.numpadMode === "price") {
            this.pos.numpadMode = "quantity";
        }
        const buttons = super.getNumpadButtons(...arguments);
        return buttons.map((button) => {
            if (button.value === "discount" && this.isDiscountRestricted) {
                return {
                    ...button,
                    disabled: true,
                    class: (button.class || "").replace("active", ""),
                };
            }
            if (button.value === "price" && this.isPriceRestricted) {
                return {
                    ...button,
                    disabled: true,
                    class: (button.class || "").replace("active", ""),
                };
            }
            return button;
        });
    },
    onNumpadClick(buttonValue) {
        if (buttonValue === "discount" && this.isDiscountRestricted) {
            return;
        }
        if (buttonValue === "price" && this.isPriceRestricted) {
            return;
        }
        return super.onNumpadClick(...arguments);
    },
});

patch(PosStore.prototype, {
    async setDiscountFromUI(line, val) {
        if (isButtonRestricted(this, "Discount")) {
            return;
        }
        return super.setDiscountFromUI(...arguments);
    },
});

patch(PosAccessRightPlugin.prototype, {
    get canApplyDiscount() {
        const pos = this.pos || this.env?.services?.pos;
        if (pos && isButtonRestricted(pos, "Discount")) {
            return false;
        }
        return super.canApplyDiscount;
    },
});
