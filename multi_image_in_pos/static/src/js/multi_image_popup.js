// Popup for Multiple Images
odoo.define('multi_image_in_pos.MultiImagePopup', function(require) {
    'use strict';
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    class MultiImagePopup extends AbstractAwaitablePopup {
         // Adds product in to order line
         confirm() {
            var product = this.props.product;
            var order = this.env.pos.get_order();
            order.add_product(product);
            this.cancel();
        }
    }
    MultiImagePopup.template = 'MultiImagePopup';
    Registries.Component.add(MultiImagePopup);
    return MultiImagePopup;
});
