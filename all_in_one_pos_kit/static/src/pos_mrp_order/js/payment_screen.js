/** @odoo-module **/
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    async _finalizeValidation() {
        this.createMRP();
        await super._finalizeValidation(...arguments);
    },

    createMRP() {
        const order = this.currentOrder;
        const products_to_mrp = [];
        for (const line of order.lines) {
            if (line.product_id && line.qty > 0 && line.product_id.to_make_mrp) {
                products_to_mrp.push({
                    'id': line.product_id.id,
                    'qty': line.qty,
                    'product_tmpl_id': line.product_id.product_tmpl_id.id || line.product_id.product_tmpl_id,
                    'pos_reference': order.name,
                    'uom_id': line.product_id.uom_id.id || line.product_id.uom_id,
                });
            }
        }
        if (products_to_mrp.length) {
            this.env.services.orm.call('mrp.production', 'create_mrp_from_pos', [products_to_mrp]);
        }
    },
});
