/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

patch(PaymentScreen.prototype, {
    /**
     * Validate the order, then create the manufacturing orders of the
     * products that are flagged "To Create MRP Order".
     */
    async validateOrder(isForceValidate) {
        const order = this.currentOrder;
        const productList = [];
        for (const orderLine of order.getOrderlines()) {
            const product = orderLine.product_id;
            // Only the products flagged to create a manufacturing order
            if (product && product.product_tmpl_id?.to_make_mrp && orderLine.qty > 0) {
                productList.push({
                    id: product.id,
                    qty: orderLine.qty,
                    product_tmpl_id: product.product_tmpl_id.id,
                    pos_reference: order.name,
                });
            }
        }
        await super.validateOrder(...arguments);
        // Create the orders only when the POS order was really validated
        if (productList.length && order.state !== "draft") {
            await this.pos.data.call("mrp.production", "create_mrp_from_pos", [
                productList,
            ]);
        }
    },
});
