/** @odoo-module */
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
import { MembershipPopup } from "@membership_in_pos/js/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";

patch(PaymentScreen.prototype, {
    async setup() {
        super.setup(...arguments);
        this.state = useState({
            membershipValues : false
        })
        this.orm = useService('orm');
        this.membershipValues = await Promise.all([
            this.orm.call("ir.config_parameter", "get_param", ["membership_in_pos.is_pos_module_pos_membership"]),
            this.orm.call("ir.config_parameter", "get_param", ["membership_in_pos.pos_membership_product_id"])
        ]);
        this.state.membershipValues = JSON.parse(this.membershipValues[0].toLowerCase())
    },

    async MembershipButton() {
          const { confirmed } = await this.popup.add(MembershipPopup, {
            title: _t("Membership Card")
            });

    }
});
