/** @odoo-module */
import { PaymentScreenStatus } from "@point_of_sale/app/screens/payment_screen/payment_status/payment_status";
import { CustomButtonPopup } from "@advanced_loyalty_management/app/loyalty_program/pos_loyalty";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";


patch(PaymentScreenStatus.prototype, {

    setup() {
        super.setup();
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.notification = useService("notification");
    },
    get hasChangeToConvert() {
        return !!this.order && Math.abs(this.order.change || 0) >= 0.005;
    },

    async convertLoyalty() {
        if (this.isRemaining || !this.hasChangeToConvert) {
            this.notification.add(_t("There is no change amount to convert to loyalty points."), {
                title: _t("Validation Error"),
                type: "danger",
            });
            return;
        }
        const order = this.order;
        await this.dialog.add(CustomButtonPopup, {
            title: _t("Loyalty Cards"),
            loyalty_points: order.getLoyaltyPoints(),
            change: order.change,
            order: order,
            pos: this.pos,
            closePopup: _t("Cancel"),
        });
    }
});
