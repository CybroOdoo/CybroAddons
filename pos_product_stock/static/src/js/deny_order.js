/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { _t } from "@web/core/l10n/translation";

patch(ProductScreen.prototype, {
    async addProductToOrder(product) {
        if (!product) {
            return super.addProductToOrder(...arguments);
        }

        const denyLimit = product.deny ?? 0;

        if (product.type === "consu" || product.type === "product" || denyLimit > 0) {
            const currentStock = this.pos.getProductStockQty(product);

            if (currentStock <= denyLimit) {
                await this.dialog.add(AlertDialog, {
                    title: _t("Deny Order"),
                    body: _t("%s is Out Of Stock", product.display_name || product.name),
                });
                return;
            }
        }

        return await super.addProductToOrder(...arguments);
    },
});
