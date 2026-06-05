/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(PosStore.prototype, {
    async pay() {
        const currentOrder = this.get_order();

        if (currentOrder && currentOrder.customer_payment_created) {
            this.notification.add(
                _t("A customer payment was already created. Start a new order to use the standard POS payment flow."),
                { type: "warning" }
            );
            return;
        }

        return super.pay(...arguments);
    },
});
