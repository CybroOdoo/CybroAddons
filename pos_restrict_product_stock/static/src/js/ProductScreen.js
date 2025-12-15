/** @odoo-module **/
/*
 * This file is used to restrict out of stock product from ordering and show restrict popup
 */
import Registries from 'point_of_sale.Registries';
import ProductScreen from 'point_of_sale.ProductScreen';

const RestrictProductScreen = (ProductScreen) => class RestrictProductScreen extends ProductScreen {
    async _clickProduct(event) {
        const product = event.detail;
        const type = this.env.pos.config.stock_type;
        const is_restrict = this.env.pos.config.is_restrict_product;
        if (product.detailed_type === 'service' || product.to_weight) {
            return super._clickProduct(event);
        }
        let qty = 0;

        const selectedLine = this.currentOrder.selected_orderline;
        if (selectedLine && selectedLine.product.id === product.id) {
            qty = selectedLine.quantity + 1;
        } else {
            qty = 1;
        }


        const qty_available = product.qty_available;
        const virtual_qty = product.virtual_available;

        const should_restrict =
            is_restrict && (
                (type === 'qty_on_hand' && qty > qty_available) ||
                (type === 'virtual_qty' && qty > virtual_qty) ||
                (qty > qty_available && qty > virtual_qty)
            );

        if (should_restrict) {
            await this.showPopup("RestrictStockPopup", {
                body: product.display_name,
                pro_id: product.id,
            });
        } else {
            await super._clickProduct(event);
        }
    }
    async _onClickPay() {
        const type = this.env.pos.config.stock_type;
        const is_restrict = this.env.pos.config.is_restrict_product;
        const body = [];
        const orderlines = this.env.pos.selectedOrder.orderlines;

        const productQtyMap = {};

        for (const line of orderlines) {
            const productId = line.product.id;
            if (!productQtyMap[productId]) {
                productQtyMap[productId] = {
                    name: line.product.display_name,
                    product: line.product,
                    total_qty: 0,
                };
            }
            productQtyMap[productId].total_qty += line.quantity;
        }

        for (const { product, name, total_qty } of Object.values(productQtyMap)) {
            if (product.detailed_type === 'service' || product.to_weight) {
                continue;
            }
            const qty_available = product.qty_available;
            const virtual_qty = product.virtual_available;

            const should_restrict = is_restrict && (
                (type === 'qty_on_hand' && total_qty > qty_available) ||
                (type === 'virtual_qty' && total_qty > virtual_qty) ||
                (total_qty > qty_available && total_qty > virtual_qty)
            );

            if (should_restrict) {
                body.push(name);
            }
        }

        if (body.length > 0) {
            const { confirmed } = await this.showPopup("RestrictStockPopup", {
                body: body.join(', '),
                pro_id: false,
            });
            if (confirmed != false) {
                return super._onClickPay(...arguments);
            } else {
                return;
            }
        }

        return super._onClickPay(...arguments);
    }
}
Registries.Component.extend(ProductScreen, RestrictProductScreen);
