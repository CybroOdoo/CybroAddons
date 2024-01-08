odoo.define('point_of_sale.ClickProductDiscount', function(require) {
    'use strict';

    const Registries = require("point_of_sale.Registries");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    var rpc = require('web.rpc');

    const ClickProductDiscount = (ProductScreen) =>
    class extends ProductScreen{
        /**
        * Function executes when product is added to the pos orderLine and checks if the
        * customer is eligible for birthday discount and triggers the set discount function
        * to set the discount percentage.
        *
        * @param {Object} event Details of the product added to the orderline
        */
        async _clickProduct(event) {
            if(this.env.pos.config.birthday_discount && this.currentOrder.attributes.client){
                var val = this.env.pos.config.discount * 100;
                for (let order_line of this.currentOrder.orderlines.models){
                    if(order_line.product.id == event.detail.id){
                        var qty = order_line.quantity + 1;
                        order_line.set_quantity(qty)
                        return;
                    }
                }
//                Code of original function
                if (!this.currentOrder) {
                    this.env.pos.add_new_order();
                }
                const product = event.detail;
                const options = await this._getAddProductOptions(product);
                // Do not add product if options is undefined.
                if (!options) return;
                // Add the product after having the extra information.
                this.currentOrder.add_product(product, options);
                NumberBuffer.reset();
//                End of original function code
                var self = this;
                var first_order = self.env.pos.config.first_order;
                var partner_id = self.currentOrder.attributes.client.id;
                await rpc.query({model: "pos.config", method: "check_pos_order", args: [[partner_id,first_order]]
                })
                .then(function (data) {
                    if(data['birthday'] == 'True' && data['order'] == 'False'){
                        self.currentOrder.get_selected_orderline().set_discount(val);
                    }
                });
            }
            else {
                if (!this.currentOrder) {
                    this.env.pos.add_new_order();
                }
                const product = event.detail;
                const options = await this._getAddProductOptions(product);
                // Do not add product if options is undefined.
                if (!options) return;
                // Add the product after having the extra information.
                this.currentOrder.add_product(product, options);
                NumberBuffer.reset();
            }
        }
    }
    Registries.Component.extend(ProductScreen, ClickProductDiscount);
});