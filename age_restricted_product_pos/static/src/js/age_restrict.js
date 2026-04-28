/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { _t } from "@web/core/l10n/translation";
import { ask } from "@point_of_sale/app/utils/make_awaitable_dialog";
/**
 * Adds a product line to the current order, with an additional check for age-restricted products.
 * If the product has an age restriction, a dialog will appear asking for confirmation to proceed.
 * If the user approves, the product is added to the order. Otherwise, the action is canceled.**/

patch(PosStore.prototype, {
    async addLineToCurrentOrder(vals, opt = {}, configure = true) {
        const tmpl = vals.product_tmpl_id;

        if (!tmpl) {
            return super.addLineToCurrentOrder(vals, opt, configure);
        }

        const tmplId = tmpl.raw?.id;

        if (!tmplId) {
            return super.addLineToCurrentOrder(vals, opt, configure);
        }

        const variants = tmpl.product_variant_ids;

        if (!variants || variants.length === 0) {
            return super.addLineToCurrentOrder(vals, opt, configure);
        }

        const productId = variants[0].id;

        const product = this.models["product.product"].records.get(productId);

        if (!product) {
            return super.addLineToCurrentOrder(vals, opt, configure);
        }

        const restricted = product.is_age_restrict;

        if (restricted) {
            const confirmed = await ask(this.dialog, {
                title: _t("Age Restricted Product!"),
                body: _t("This product is age restricted. Do you want to continue?"),
                cancelLabel: _t("Reject"),
                confirmLabel: _t("Approve"),
            });

            if (!confirmed) return;
        }

        return super.addLineToCurrentOrder(vals, opt, configure);
    },
});
