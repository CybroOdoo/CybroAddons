/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {
    ProductConfiguratorPopup
} from "@point_of_sale/app/components/popups/product_configurator_popup/product_configurator_popup";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {_t} from "@web/core/l10n/translation";

patch(ProductConfiguratorPopup.prototype, {
    async confirm() {
        const product = this.product;
        const posConfig = this.pos.config;
        const dialog = this.env.services.dialog;
        if (!product) {
            return super.confirm(...arguments);
        }

        if (!posConfig.is_restrict_product) {
            return super.confirm(...arguments);
        }

        const qtyAvailable = product.qty_available || 0;
        const forecastQty = product.virtual_available || 0;

        let outOfStock = false;

        switch (posConfig.stock_type) {
            case "qty_on_hand":
                outOfStock = qtyAvailable <= 0;
                break;

            case "virtual_qty":
                outOfStock = forecastQty <= 0;
                break;

            case "both":
                outOfStock =
                    qtyAvailable <= 0 ||
                    forecastQty <= 0;
                break;
        }

        if (outOfStock) {
            const confirmed = await new Promise((resolve) => {
                dialog.add(ConfirmationDialog, {
                    title: _t("Out of Stock"),
                    body: _t(
                        "%s is out of stock. Do you want to proceed?"
                    ).replace("%s", product.display_name),
                    confirmLabel: _t("Order"),
                    cancelLabel: _t("Cancel"),
                    confirm: () => resolve(true),
                    cancel: () => resolve(false),
                });
            });

            if (!confirmed) {
                return;
            }
        }
        return super.confirm(...arguments);
    },
});