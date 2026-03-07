/** @odoo-module */
/**
 * Patch the OrderReceipt component in POS
 * to add computed values for total items and total quantity.
 */
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { patch } from "@web/core/utils/patch";
patch(OrderReceipt.prototype, {
    /**
     * Getter for total number of distinct order lines.
    */
    get itemsCount() {
        const count = this.props.order.lines.length;
        return count;
    },
    /**
     * Getter for total quantity of all products in the order.
     */
    get itemsTotalQty() {
        const total = this.props.order.lines.reduce(
            (sum, line) => sum + line.qty,
            0
        );
        return total;
    },
});
