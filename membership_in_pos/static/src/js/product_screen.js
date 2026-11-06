import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { PosStore } from "@point_of_sale/app/services/pos_store";

patch(PosStore.prototype, {
    async addLineToOrder(vals, order, opts = {}, configure = true) {
        // Guard: ensure product_tmpl_id has valid product_variant_ids
        const productTmpl = typeof vals.product_tmpl_id === "number"
            ? this.data.models["product.template"].get(vals.product_tmpl_id)
            : vals.product_tmpl_id;
        if (productTmpl && (!productTmpl.product_variant_ids || !productTmpl.product_variant_ids.length || !productTmpl.product_variant_ids[0])) {
            this.dialog.add(AlertDialog, {
                title: _t("Product Unavailable"),
                body: _t("This product has no available variants. Please check the product configuration."),
            });
            return;
        }
        return await super.addLineToOrder(vals, order, opts, configure);
    },
    async pay() {
        const current_order = this.getOrder();
        const partner = current_order.getPartner();

        if (!partner) {
            this.dialog.add(AlertDialog, {
                title: _t("Customer Required"),
                body: _t("You must select a customer before proceeding to payment."),
            });
            return;
        }

        return await super.pay();
    },

});