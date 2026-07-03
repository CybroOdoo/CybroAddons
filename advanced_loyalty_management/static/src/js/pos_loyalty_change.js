/** @odoo-module */
import { PaymentScreenStatus } from "@point_of_sale/app/screens/payment_screen/payment_status/payment_status";
import { CustomButtonPopup } from "@advanced_loyalty_management/app/loyalty_program/pos_loyalty";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";


patch(PaymentScreenStatus.prototype, {

    setup() {
     super.setup();
        this.pos = usePos();
        this.dialog = useService("dialog");
    },

    async convertLoyalty(){
        //---A popup added when convert to loyalty button is clicked---
       const order = this.pos.get_order();
           await this.dialog.add(CustomButtonPopup, {
               title: _t("Loyalty Cards"),
               loyalty_points: order.getLoyaltyPoints(),
               change: order.get_change(),
               order: order,
               pos: this.pos,
            });
       }
});
