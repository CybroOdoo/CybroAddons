/** @odoo-module */

console.log("🔴 DEBUG: This should appear in console");
import { patch } from "@web/core/utils/patch";
// CORRECT IMPORT: Import from the core point_of_sale module
import { OrderDisplay } from "@point_of_sale/app/components/order_display/order_display";


patch(OrderDisplay.prototype, {


    get ItemCount(){
        return this.lines.length
    },

    get TotalQuantity(){
        var totalQuantity = 0;
        console.log("totalQuantity",totalQuantity);

        this.lines.forEach((line) => {
            totalQuantity += line.qty
        });
        this.qty = totalQuantity
        return totalQuantity
    }
});
