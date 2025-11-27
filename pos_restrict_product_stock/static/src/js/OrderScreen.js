    /** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import RestrictStockPopup from "@pos_restrict_product_stock/js/RestrictStockPopup"

patch(Order.prototype, {
    async pay() {
        const type = this.pos.config.stock_type;
        const is_restrict = this.pos.config.is_restrict_product;
        const body = [];
        const productQuantities = {};

        for (const line of this.orderlines) {
            const productId = line.product.id;
            if (!productQuantities[productId]) {
                productQuantities[productId] = {
                    name: line.product.display_name,
                    product: line.product,
                    total_qty: 0,
                };
            }
            productQuantities[productId].total_qty += line.quantity;
        }

        for (const { product, total_qty, name } of Object.values(productQuantities)) {
               if (product.detailed_type === 'service'|| product.to_weight) {
                continue;
            }
            if (is_restrict) {
                const qty_available = product.pos_stock_qty ?? product.qty_available;
                const virtual_qty = product.virtual_available;

                const should_restrict = (
                    (type === 'qty_on_hand' && total_qty > qty_available) ||
                    (type === 'virtual_qty' && total_qty > virtual_qty) ||
                    (total_qty > qty_available && total_qty > virtual_qty)
                );

                if (should_restrict) {
                    body.push(name);
                }
            }
        }
        if (body.length > 0) {
            const confirmed = await this.pos.popup.add(RestrictStockPopup, {
                body: body.join(', '),
                pro_id: false
            });

            if (confirmed === true) {
                return super.pay();
            } else {
                return;
            }
        }
        return super.pay();
    }
})