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
        if (current_order.pos.table['reserved'] == true && current_order.orderlines.length == 0){
            var data = this.orm.call('table.reservation', 'add_payment', [current_order.pos.table.id, current_order.pos.table.floor.id])
            data.then(result => {
                productDetails.push({
                    product_id: result.product,
                    rate: result.rate
                });
                // Adding payment to the table during the reservation
                var product = this.pos.db.product_by_id[productDetails[0].product_id]
                product['lst_price'] = productDetails[0].rate
                if (current_order.orderlines.length == 0){
                    console.log('prodsss', product['lst_price'])
                    this.pos.get_order().add_product(product, {
                        quantity: 1,
                    });
                }
            })
        }
        return this.pos.get_order();
    }
});
