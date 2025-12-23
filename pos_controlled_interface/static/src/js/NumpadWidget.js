/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
patch(ProductScreen.prototype, {
    getNumpadButtons() {
            return [
                { value: "1" },
                { value: "2" },
                { value: "3" },
                { value: "quantity", text: _t("Qty") },
                { value: "4" },
                { value: "5" },
                { value: "6" },
                { value: "discount", text: _t("% Disc"), disabled: !this.pos.config.manual_discount || this.pos.config.control_discount},
                { value: "7" },
                { value: "8" },
                { value: "9" },
                {
                    value: "price",
                    text: _t("Price"),
                    disabled: !this.pos.cashierHasPriceControlRights() || this.pos.config.control_price,
                },
                { value: "-", text: "+/-" },
                { value: "0" },
                { value: this.env.services.localization.decimalPoint },
                // Unicode: https://www.compart.com/en/unicode/U+232B
                { value: "Backspace", text: "⌫" },
            ].map((button) => ({
                ...button,
                class: this.pos.numpadMode === button.value ? "active border-primary" : "",
            }));
        }
})
