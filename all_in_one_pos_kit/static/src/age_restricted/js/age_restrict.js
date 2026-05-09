/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { ask } from "@point_of_sale/app/store/make_awaitable_dialog";
/**
 * Adds a product line to the current order, with an additional check for age-restricted products.
 * If the product has an age restriction, a dialog will appear asking for confirmation to proceed.
 * If the user approves, the product is added to the order. Otherwise, the action is canceled.**/

patch(PosStore.prototype, {
    async addLineToCurrentOrder(vals, opts = {}, configure = true) {
        let product = vals.product_id;
        if (typeof product === "number") {
            product = this.models["product.product"].get(product);
        }
        if (product?.is_age_restrict) {
            const confirmed = await ask(this.dialog, {
                title: _t("Age Restricted Product !!!!!!"),
                body: _t("Please get Identity proof from customer."),
                cancelLabel: _t("Cancel"),
                confirmLabel: _t("Ok"),
            });
            if (!confirmed) {
                return;
            }
        }
        return super.addLineToCurrentOrder(vals, opts, configure);
    },
});
