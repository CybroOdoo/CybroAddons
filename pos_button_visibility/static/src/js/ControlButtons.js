/** @odoo-module */

import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { getRestrictedPosButtons } from "@pos_button_visibility/js/numpad_button";

patch(ControlButtons.prototype, {
    isPosButtonRestricted(buttonName) {
        return getRestrictedPosButtons(this.pos).has(buttonName);
    },

    clickRefund() {
        if (this.isPosButtonRestricted("Refund")) {
            return;
        }
        return super.clickRefund(...arguments);
    },

    clickRewards() {
        if (this.isPosButtonRestricted("Reward")) {
            return;
        }
        return super.clickRewards(...arguments);
    },
});
