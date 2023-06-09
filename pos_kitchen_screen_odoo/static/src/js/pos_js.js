odoo.define('pos_kitchen_screen_odoo.SubmitOrderButtons', function(require) {
    "use strict";
    var SubmitOrderButton = require('pos_restaurant.SubmitOrderButton');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    //Extending the SubmitOrderButton to change the condition of seeing the order button in the pos session and create orders
    class SubmitOrderButtonButton extends SubmitOrderButton {

        async _onClick() {
            if (!this.clicked) {
                try {
                    this.clicked = true;
                    const order = this.env.pos.get_order();
                    var self = this;
                    var line = []

                    for (const orders of this.currentOrder.orderlines) {
                        line.push([0, 0, {
                            'qty': orders.quantity,
                            'price_unit': orders.price,
                            'price_subtotal': orders.quantity * orders.price,
                            'price_subtotal_incl': orders.quantity * orders.price,
                            'discount': orders.discount,
                            'product_id': orders.product.id,
                            'tax_ids': [
                                [6, false, []]
                            ],
                            'id': 29,
                            'pack_lot_ids': [],
                            'full_product_name': orders.product.display_name,
                            'price_extra': orders.price_extra,
                            'name': 'newsx/0031',
                            'is_cooking': true
                        }])
                    }
                    var orders = [{
                        'pos_reference': this.currentOrder.name,
                        'session_id': this.currentOrder.pos_session_id,
                        'amount_total': 0,
                        'amount_paid': 0,
                        'amount_return': '0',
                        'amount_tax': 2.18,
                        'lines': line,
                        'is_cooking': true,
                        'order_status': 'draft',
                        'company_id': this.env.pos.company.id,
                        'pricelist_id': this.env.pos.pricelists[0].id
                    }]
                    self.rpc({
                        model: 'pos.order',
                        method: 'get_details',
                        args: [
                            [], self.env.pos.config.id, orders
                        ],
                    })
                } finally {
                    this.clicked = false;
                }
            }
        }
        get currentOrder() {
            return this.env.pos.get_order();
        }
        get addedClasses() {
            return {};
        }
    }
    SubmitOrderButtonButton.template = 'SubmitOrderButtons';
    ProductScreen.addControlButton({
        component: SubmitOrderButtonButton,
         condition: function() {
            return this.env.pos.config.module_pos_restaurant;
        },
    });
    Registries.Component.add(SubmitOrderButtonButton);
    return SubmitOrderButtonButton;
});