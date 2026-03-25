/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { CalculatorPopup } from "@calculator_in_pos/app/calculator_popup/calculator_popup";
import { _t } from "@web/core/l10n/translation";

patch(ControlButtons.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialog = useService("dialog");
    },

    async onClick() {
        this.dialog.add(CalculatorPopup, {
            title: _t('Calculator'),
        })
    }
});
