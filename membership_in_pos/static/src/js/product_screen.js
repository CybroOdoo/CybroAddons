/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { PosStore } from "@point_of_sale/app/services/pos_store";

patch(PosStore.prototype, {
    _proceedToPayment() {
        this.env.services.pos.mobile_pane = "right";
        this.navigate("PaymentScreen", {
            orderUuid: this.selectedOrderUuid,
        });
    },
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
                title: _t("Customer"),
                body: _t("You Must Select a Customer"),
            });
            return;
        }
        const hasInvalidLot = current_order.getOrderlines().some(
            (line) =>
                line.getProduct().tracking !== "none" &&
                !line.hasValidProductLot()
        );

        if (
            hasInvalidLot &&
            (this.env.services.pos.pickingType.use_create_lots ||
                this.env.services.pos.pickingType.use_existing_lots)
        ) {
            this.dialog.add(ConfirmationDialog, {
                title: _t("Some Serial/Lot Numbers are Missing"),
                body: _t(
                    "You are trying to sell products with serial/lot numbers, but some of them are not set.\nWould you like to proceed anyway?"
                ),
                confirm: () => {
                    this._proceedToPayment();
                },
                cancel: () => {

                },
            });
        } else {
            this._proceedToPayment();
        }
        return await super.pay();
    },

});