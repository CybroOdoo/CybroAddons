/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { _t } from "@web/core/l10n/translation";
import { ask } from "@point_of_sale/app/utils/make_awaitable_dialog";

/**
 * Adds a product line to the current order, with an additional check for
 * age-restricted products. If the product is age restricted, a dialog asks
 * for confirmation. If it is rejected, the product is not added.
 */
patch(PosStore.prototype, {
    // Resolve a record or an id to a record of the given model
    _ageLookup(model, value) {
        if (!value) {
            return null;
        }
        if (typeof value === "object") {
            return value;
        }
        return this.models[model]?.get(value) || null;
    },

    _isAgeRestricted(vals) {
        const product = this._ageLookup("product.product", vals?.product_id);
        const tmpl =
            this._ageLookup("product.template", vals?.product_tmpl_id) ||
            product?.product_tmpl_id ||
            null;
        if (product?.is_age_restrict || tmpl?.is_age_restrict) {
            return true;
        }
        // flag stored on one of the variants of the template
        const variants = tmpl?.product_variant_ids;
        return !!(variants && Array.from(variants).some((v) => v?.is_age_restrict));
    },

    async addLineToCurrentOrder(vals, opt = {}, configure = true) {
        if (this._isAgeRestricted(vals)) {
            const confirmed = await ask(this.dialog, {
                title: _t("Age Restricted Product!"),
                body: _t("This product is age restricted. Do you want to continue?"),
                cancelLabel: _t("Reject"),
                confirmLabel: _t("Approve"),
            });
            if (!confirmed) {
                return;
            }
        }
        return super.addLineToCurrentOrder(vals, opt, configure);
    },
});
