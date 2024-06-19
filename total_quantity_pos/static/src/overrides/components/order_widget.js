/** @odoo-module */

import { OrderWidget } from "@point_of_sale/app/generic_components/order_widget/order_widget";
import { patch } from "@web/core/utils/patch";

// Patch the OrderSummary to add custom properties
patch(OrderWidget.prototype, {
     /**
     * Get the total number of items in the order.
     *
     * @returns {number} The total number of items in the order.
     */
    get ItemCount(){
       return this.props.lines.length
    },
     /**
     * Get the total quantity of items in the order.
     *
     * @returns {number} The total quantity of items in the order.
     */
    get TotalQuantity(){
        var totalQuantity = 0;
        this.props.lines.forEach(line => totalQuantity += line.quantity);
        return totalQuantity
    }
});
