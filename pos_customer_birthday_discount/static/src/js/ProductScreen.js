/** @odoo-module */

import Registries from "point_of_sale.Registries";
import ProductScreen from "point_of_sale.ProductScreen";
import rpc from 'web.rpc';

const discount = (ProductScreen) =>
class extends ProductScreen{
    /**
    * Function executes when product is added to the pos orderLine and checks if the
    * customer is eligible for birthday discount and triggers the set discount function
    * to set the discount percentage.
    *
    * @param {Object} product Product object that is added to orderLine
    * @param {Object} options other details while adding product
    */
    async _addProduct(product, options) {
        if(this.env.pos.config.birthday_discount && this.currentOrder.partner){
            var val = this.env.pos.config.discount * 100;
            for (let order_line of this.currentOrder.orderlines){
                if(order_line.product.id == product.id){
                    var qty = order_line.quantity + 1;
                    order_line.set_quantity(qty)
                    return;
                }
            }
            this.currentOrder.add_product(product, options);
            var self = this;
            var first_order = self.env.pos.config.first_order;
            var partner_id = self.currentOrder.partner.id;
            await rpc.query({model: "pos.config", method: "check_pos_order", args: [partner_id,first_order]
            })
            .then(function (data) {
                if(data['birthday'] == 'True' && data['order'] == 'False'){
                    self.currentOrder.get_selected_orderline().set_discount(val);
                }
            });
        }
        else{
            this.currentOrder.add_product(product, options);
        }
    }
}
Registries.Component.extend(ProductScreen, discount);
