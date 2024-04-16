/** @odoo-module */
import { PaymentScreenStatus } from "@point_of_sale/app/screens/payment_screen/payment_status/payment_status";
import { CustomButtonPopup } from "@advanced_loyalty_management/js/pos_loyalty_popups";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { _t } from "@web/core/l10n/translation";

patch(PaymentScreenStatus.prototype, {

    setup() {
       this.pos = usePos();
       this.popup = useService("popup");
    },

    async convertLoyalty(){
        //---a popup added when convert to loyalty button is clicked---
       const order = this.pos.get_order();
       await this.popup.add(CustomButtonPopup, {
           title: _t("Loyalty Cards"),
           loyalty_points: order.getLoyaltyPoints(),
           change: order.get_change(),
           order: order,
           pos: this.pos,
       });
    }
});
