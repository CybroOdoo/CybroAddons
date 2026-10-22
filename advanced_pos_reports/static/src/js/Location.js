/** @odoo-module **/
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { LocationSummaryPopup } from "./LocationPopup";

patch(ControlButtons.prototype, {
    async onClickLocationSummary() {
        await this.dialog.add(LocationSummaryPopup, {
            title: _t("Location Summary"),
        });
    },
});
