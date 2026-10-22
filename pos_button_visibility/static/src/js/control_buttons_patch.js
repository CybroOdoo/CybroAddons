/** @odoo-module */
/**
 * Patch: ControlButtons (POS Product Screen)
 *
 * Restricts the Reward control button based on the logged-in cashier's
 * button visibility settings and POS configuration.
 */
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { isButtonRestricted } from "@pos_button_visibility/js/utils";

patch(ControlButtons.prototype, {
    get isRewardRestricted() {
        return isButtonRestricted(this.pos, "Reward");
    },
    getPotentialRewards() {
        if (this.isRewardRestricted) {
            return [];
        }
        return super.getPotentialRewards ? super.getPotentialRewards(...arguments) : [];
    },
    async clickRewards() {
        if (this.isRewardRestricted) {
            return;
        }
        if (super.clickRewards) {
            return super.clickRewards(...arguments);
        }
    },
});
