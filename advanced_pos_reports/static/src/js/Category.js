/** @odoo-module **/
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { CategorySummaryPopup } from "./CategoryPopup";

patch(ControlButtons.prototype, {
    async onClickCategorySummary() {
        await this.dialog.add(CategorySummaryPopup, {
            title: _t("Category Summary"),
        });
    },
});
