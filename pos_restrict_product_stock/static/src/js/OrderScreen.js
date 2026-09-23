/** @odoo-module */
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(PosStore.prototype, {
    async pay() {
        if (!this.config?.is_restrict_product) {
            return super.pay();
        }
        const type = this.config.stock_type;
        const outOfStockProducts = [];
        const currentOrder = this.getOrder();
        if (currentOrder) {
            for (const line of currentOrder.getOrderlines()) {
                const product = line.product_id;
                if (!product || product.type === 'service' || product.to_weight) {
                    continue;
                }
                const qty = product.qty_available ?? 0;
                const virtualQty = product.virtual_available ?? 0;
                const isOutOfStock =
                    (type === 'qty_on_hand' && qty <= 0) ||
                    (type === 'virtual_qty' && virtualQty <= 0) ||
                    (type === 'both' && (qty <= 0 || virtualQty <= 0));

                if (isOutOfStock) {
                    outOfStockProducts.push(product.display_name || product.name || "");
                }
            }
        }
        if (outOfStockProducts.length > 0) {
            const confirmed = await new Promise((resolve) => {
                this.dialog.add(ConfirmationDialog, {
                    title: _t("Out of Stock Warning"),
                    body: _t("%s is out of stock. Click Order if you still want to process this order?").replace("%s", outOfStockProducts.join(", ")),
                    confirmLabel: _t("Order"),
                    cancelLabel: _t("Cancel"),
                    confirm: () => resolve(true),
                    cancel: () => resolve(false),
                });
            });
            if (confirmed) {
                return super.pay();
            }
        } else {
            return super.pay();
        }
    }
});
