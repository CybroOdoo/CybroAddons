/** @odoo-module */
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
import { MembershipPopup } from "@membership_in_pos/js/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { PosOrder } from "@point_of_sale/app/models/pos_order";

patch(PosOrder.prototype, {
    getChange() {
        return this.change;
    }
});


patch(PaymentScreen.prototype, {
    async setup() {
        super.setup(...arguments);
        this.state = useState({
            membershipValues: false
        })
        this.orm = useService('orm');
        this.membershipValues = await Promise.all([
            this.orm.call("ir.config_parameter", "get_param", ["membership_in_pos.is_pos_module_pos_membership"]),
            this.orm.call("ir.config_parameter", "get_param", ["membership_in_pos.pos_membership_product_id"])
        ]);
        this.state.membershipValues = this.membershipValues[0] ? JSON.parse(this.membershipValues[0].toLowerCase()) : false;
    },

    async MembershipButton() {
        this.dialog.add(MembershipPopup, {
            title: _t("Membership Card"),
        });

    }
});
