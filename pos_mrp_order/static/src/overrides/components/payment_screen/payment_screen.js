/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

patch(PaymentScreen.prototype, {

    async validateOrder(isForceValidate) {
        const orderLines = this.currentOrder.getOrderlines();
        let productList = [];
        for (const orderLine of orderLines) {
            // Check if order line has valid product and positive quantity
            if (orderLine.product_id && orderLine.qty > 0) {
                const productDict = {
                    'id': orderLine.product_id.id,
                    'qty': orderLine.qty,
                    'product_tmpl_id': orderLine.product_id.product_tmpl_id.id,
                    'pos_reference': this.currentOrder.name,
                };
                productList.push(productDict);
            }
        }
        // Make a single API call with all products
        this.pos.data.call('mrp.production', 'create_mrp_from_pos', [productList])
        return super.validateOrder(...arguments);
    }

});
