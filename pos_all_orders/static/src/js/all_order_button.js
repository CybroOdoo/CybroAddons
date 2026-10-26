/** @odoo-module **/
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { ComboSuggestion } from "@point_of_sale/app/models/utils/combo_suggestion";

patch(ComboSuggestion.prototype, {
    _getProductOrderMap(order) {
        if (!order) {
            return {};
        }
        return super._getProductOrderMap(...arguments);
    },
    getApplicableProductCombo(order, mode = "limited") {
        if (!order) {
            return [];
        }
        return super.getApplicableProductCombo(...arguments);
    },
    getPotentialCombos(order) {
        if (!order) {
            return [];
        }
        return super.getPotentialCombos(...arguments);
    },
});

patch(ControlButtons.prototype, {
    onAllOrdersClick() {
        const currentOrder = this.pos.getOrder();
        this.pos.navigate("CustomALLOrdrScreen", {
            orderUuid: currentOrder?.uuid,
        });
    },
});