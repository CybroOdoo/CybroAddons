/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { getOnNotified } from "@point_of_sale/utils";
import { ask } from "@point_of_sale/app/utils/make_awaitable_dialog";

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        this.kitchen = true;
        this.pos = this.env.services["pos"]; // ✅ get pos service if needed
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
                title: _t("No category found"),
                body: _t(
                    `No food items found for the specified category (${result.category}) for this kitchen.
                    Please remove the selected food, update the order by clicking the 'Order' button,
                    and then proceed with the payment.`
                ),
            });
            return;
        }

        if (result === true) {
            this.kitchen = false;
            await this.env.services.dialog.add(AlertDialog, {
                title: _t("Food is not ready"),
                body: _t("Please complete all the food first."),
            });
            return;
        } else {
            this.kitchen = true;
        }

        if (!order.canPay()) {
            return;
        }

        if (
            order.lines.some(
                (line) =>
                    line.getProduct().tracking !== "none" &&
                    !line.has_valid_product_lot()
            ) &&
            (this.pickingType.use_create_lots || this.pickingType.use_existing_lots) &&
            result === false
        ) {
            const confirmed = await ask(this.env.services.dialog, {
                title: _t("Some Serial/Lot Numbers are missing"),
                body: _t(
                    "You are trying to sell products with serial/lot numbers, but some of them are not set.\nWould you like to proceed anyway?"
                ),
            });
            if (!confirmed) {
                return;
            }
        }
        super.pay()
    },
});
