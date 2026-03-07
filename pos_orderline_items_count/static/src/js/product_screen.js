/** @odoo-module */
import { OrderDisplay } from "@point_of_sale/app/components/order_display/order_display";
import { patch } from "@web/core/utils/patch";
patch(OrderDisplay.prototype, {
     /**
     * Get the total number of items in the order.
     */
    get ItemCount(){
       return this.props.order.lines.length

    },
     /**
     * Get the total quantity of items in the order.
     */
    get TotalQuantity(){
        var totalQuantity = 0;
        this.props.order.lines.forEach(line => totalQuantity += line.qty);
        return totalQuantity
    }
});
