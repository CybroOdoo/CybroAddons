/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { FeedbackPopup } from "./feedback_popup";

/* Patching ControlButtons and adding Feedback button */
patch(ControlButtons.prototype, {
    /* Function while clicking the button */
    async onClick() {
        const order = this.pos.getOrder();
        if (order && order.getPartner() && order.lines.length > 0){
            await this.dialog.add(
                FeedbackPopup, {
                    startingComment: order.comment_feedback,
                    startingRating: order.customer_feedback,
                    title: _t('Customer Feedback'),
                    pos: this.pos,
                }
            );
        }
    }
});
