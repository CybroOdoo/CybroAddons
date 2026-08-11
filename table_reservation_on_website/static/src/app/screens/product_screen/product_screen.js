/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
let productDetails = [];

patch(ProductScreen.prototype, {
    // Override the bookTable function for displaying and booking of tables
    bookTable() {
        this.pos.showScreen("ReservationsScreen");
    },
    get currentOrder() {
        let productDetails = [];
        const current_order = this.pos.get_order();
        if (current_order && current_order.table && current_order.table['reserved'] == true && current_order.orderlines.length == 0){
            var data = this.env.services.orm.call('table.reservation', 'add_payment', [current_order.table.id, current_order.table.floor.id])
            data.then(result => {
                productDetails.push({
                    product_id: result.product,
                    rate: result.rate
                });
                // Adding payment to the table during the reservation
                var product = this.pos.models['product.product'].get(productDetails[0].product_id)
                if (product) {
                    product['lst_price'] = productDetails[0].rate
                    if (current_order.orderlines.length == 0){
                        if (!this.pos.get_order()) {
                            this.pos.add_new_order();
                        }
                        this.pos.addLineToCurrentOrder({
                            product_id: product,
                            price_unit: productDetails[0].rate,
                            qty: 1,
                        });
                    }
                }
            })
        }
        return this.pos.get_order();
    }
});
