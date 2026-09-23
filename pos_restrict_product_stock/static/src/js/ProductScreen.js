/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { ProductCard } from "@point_of_sale/app/components/product_card/product_card";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(ProductCard.prototype, {
    setup() {
        super.setup();
        this.pos = useService("pos");
    },
});

patch(ProductScreen.prototype, {
    setup() {
        super.setup();
        this.dialog = useService("dialog");
    },
    async addProductToOrder(product, ...args) {
        if (!product) {
            return super.addProductToOrder(product, ...args);
        }
        const type = this.pos.config.stock_type;
        const qty = product.qty_available ?? 0;
        const virtualQty = product.virtual_available ?? 0;

        const isOutOfStock =
            (type === 'qty_on_hand' && qty <= 0) ||
            (type === 'virtual_qty' && virtualQty <= 0) ||
            (type === 'both' && (qty <= 0 || virtualQty <= 0));

        if (this.pos.config.is_restrict_product && isOutOfStock && product.type !== 'service' && !product.to_weight) {
            const confirmed = await new Promise((resolve) => {
                this.dialog.add(ConfirmationDialog, {
                    title: _t("Out of Stock"),
                    body: _t("%s is out of stock. Do you want to proceed?").replace("%s", product.display_name || product.name || ""),
                    confirmLabel: _t("Order"),
                    cancelLabel: _t("Cancel"),
                    confirm: () => resolve(true),
                    cancel: () => resolve(false),
                });
            });
            if (confirmed) {
                product.order_status = true;
                return super.addProductToOrder(product, ...args);
            }
        } else {
            return super.addProductToOrder(product, ...args);
        }
    },
});
