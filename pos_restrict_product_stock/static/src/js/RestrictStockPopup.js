/** @odoo-module **/
/*
 * This file is used to store a popup for stocks out of stock for forced orders.
 */
import AbstractAwaitablePopup from 'point_of_sale.AbstractAwaitablePopup';
import Registries from 'point_of_sale.Registries';

class RestrictStockPopup extends AbstractAwaitablePopup {
    _OrderProduct() {
    // On clicking order product button on popup, it will add product to orderline
        var product = this.env.pos.db.get_product_by_id(this.props.pro_id)
        this.env.pos.selectedOrder.add_product(product);
        this.cancel();
    }
}
RestrictStockPopup.template = 'RestrictStockPopup';
Registries.Component.add(RestrictStockPopup);
