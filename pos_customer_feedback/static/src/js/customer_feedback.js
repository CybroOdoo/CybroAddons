/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { FeedbackPopup } from "./feedback_popup";

/* Patching ControlButtons and adding Feedback button */
patch(ControlButtons.prototype, {
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
    },
    /* Function while clicking the button */
    async onClick() {
        if (this.pos.get_order().partner_id && this.pos.get_order().lines){
            await this.dialog.add(
                FeedbackPopup, {
                    startingComment: this.pos.get_order().comment,
                    startingRating: this.pos.get_order().feedback,
                    title: _t('Customer Feedback'),
                    pos: this.pos,
                }
            );
        }
    }
});
