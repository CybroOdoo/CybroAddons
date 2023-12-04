odoo.define('Pos_product_stock.update', function(require) {
    'use strict';
    const ProductItem = require('point_of_sale.ProductItem');
    const Registries = require('point_of_sale.Registries');
    const Update = (ProductItem) => class extends ProductItem { //extend ProductItem and super setup() function.
        setup() {
            super.setup(...arguments);
        }
        get value() {
            if (this.env.pos.res_setting.display_stock == true) {
                const current_product = this.props.product.id
                const stock_product = this.env.pos.stock_quant
                const move_line = this.env.pos.move_line
                var qty = 0;
                var on_hand = 0;
                var outgoing = 0;
                var incoming = 0;
                var available = 0;
                stock_product.forEach((product) => {
                    if (product.product_id[0] == current_product) {
                        qty = qty + product.available_quantity;
                        on_hand = on_hand + product.quantity;
                        available = this.props.product.qty_available - this.props.product.outgoing_qty
                    }
                });
                move_line.forEach((line) => {
                    if (line.product_id[0] == current_product && this.env.pos.res_setting && this.env.pos.res_setting.stock_location_id && this.env.pos.res_setting.stock_location_id[1] == line.location_dest_id[1]) {
                        incoming = incoming + line.qty_done;
                    } else if (line.product_id[0] == current_product && this.env.pos.res_setting && this.env.pos.res_setting.stock_location_id && this.env.pos.res_setting.stock_location_id[1] == line.location_id[1]) {
                        outgoing = outgoing + line.qty_done;
                    }
                });
                if (!this.props.product.available) {
                    this.props.product.available = qty // pass value in session
                }
                if (!this.props.product.on_hand) {
                    this.props.product.on_hand = on_hand;
                }
                if (!this.props.product.outgoing) {
                    this.props.product.outgoing = outgoing
                }
                if (!this.props.product.incoming) {
                    this.props.product.incoming_loc = incoming
                }
                if (!this.props.product.available_product) {
                    this.props.product.available_product = available
                }
                return {
                    display_stock: this.env.pos.res_setting.display_stock
                }
            } else {
                return {
                    display_stock: false
                }
            }
        }
    };
    Registries.Component.extend(ProductItem, Update);
    return ProductItem;
});
