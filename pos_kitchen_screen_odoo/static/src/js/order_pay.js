/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        this.kitchen = true;
        this.pos = this.env.services["pos"];
    },


    async pay() {
        const order = this.getOrder();
        if (!order) return;

        const order_name = order.pos_reference;

        const result = await rpc("/web/dataset/call_kw/pos.order/check_order", {
            model: "pos.order",
            method: "check_order",
            args: [order_name],
            kwargs: {},
        });

        if (result.category) {
            this.kitchen = false;
            await this.env.services.dialog.add(AlertDialog, {
                title: _t("Category Not Found"),
                body: _t(
                    `The category (${result.category}) is not handled by this kitchen.
                    Please remove those items, update the order by clicking the 'Order' button,
                    and then proceed with the payment.`
                ),
            });
            return;
        }

        if (result === true) {
            this.kitchen = false;
            await this.env.services.dialog.add(AlertDialog, {
                title: _t("Food Is Not Ready"),
                body: _t("Please complete all the food items first."),
            });
            return;
        } else {
            this.kitchen = true;
        }

        return super.pay(...arguments);
    },
});
