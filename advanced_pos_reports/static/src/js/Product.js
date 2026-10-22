/** @odoo-module **/
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { ProductSummaryPopup } from "./ProductPopup";

patch(ControlButtons.prototype, {
    async onClickProductSummary() {
        await this.dialog.add(ProductSummaryPopup, {
            title: _t("Product Summary"),
        });
    },
});