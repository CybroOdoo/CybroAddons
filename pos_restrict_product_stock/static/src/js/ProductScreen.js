/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import RestrictStockPopup from "@pos_restrict_product_stock/js/RestrictStockPopup"
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";

patch(PosStore.prototype, {
    async addProductToCurrentOrder(...args) {
        const product = args[0];
         if (product.detailed_type === 'service'|| product.to_weight) {
            return super.addProductToCurrentOrder(...args);
        }
        const type = this.config.stock_type;
        const order = this.get_order();
        const selected_orderline = order.get_selected_orderline();
        let order_quantity = 1;
        if (selected_orderline && selected_orderline.product.id === product.id) {
            order_quantity = selected_orderline.quantity + 1;
        }

        const qty_available = product.pos_stock_qty ?? product.qty_available;
        const virtual_qty = product.virtual_available;

        const should_restrict =
            this.config.is_restrict_product &&
            (
                (type === 'qty_on_hand' && order_quantity > qty_available) ||
                (type === 'virtual_qty' && order_quantity > virtual_qty) ||
                (order_quantity > qty_available && order_quantity > virtual_qty)
            );

        if (should_restrict) {
            const confirmed = this.popup.add(RestrictStockPopup, {
                body: product.display_name,
                pro_id: product.id,
            });

        } else {
            await super.addProductToCurrentOrder(...args);
        }
    },
});