/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ProductConfiguratorPopup } from "@point_of_sale/app/store/product_configurator_popup/product_configurator_popup";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(ProductConfiguratorPopup.prototype, {
    async confirm() {
        const product = this.state.product;
        const posConfig = this.pos.config;
        if (!product) {
            return super.confirm(...arguments);
        }
        if (!posConfig.is_restrict_product) {
            return super.confirm(...arguments);
        }
        let outOfStock = false;
        switch (posConfig.stock_type) {
            case "qty_on_hand":
                outOfStock = product.qty_available <= 0;
                break;
            case "virtual_qty":
                outOfStock = product.virtual_available <= 0;
                break;
            case "both":
                outOfStock =
                    product.qty_available <= 0 ||
                    product.virtual_available <= 0;
                break;
        }
        if (outOfStock) {
            const confirmed = await new Promise((resolve) => {
                this.env.services.dialog.add(
                    ConfirmationDialog,
                    {
                        title: _t("Out of Stock"),
                        body: _t(
                            "%s is out of stock. Do you want to proceed?"
                        ).replace("%s", product.display_name),
                        confirmLabel: _t("Order"),
                        cancelLabel: _t("Cancel"),
                        confirm: () => resolve(true),
                        cancel: () => resolve(false),
                    }
                );
            });
            if (!confirmed) {
                return;
            }
        }
        return super.confirm(...arguments);
    },
});