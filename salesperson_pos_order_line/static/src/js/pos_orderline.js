/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { rpc } from "@web/core/network/rpc";


patch(PosOrderline.prototype, {
    /**
     * Retrieves and sets the salesperson for the current order line.
     * Checks if the order line ID is valid and performs an RPC call
     * to fetch the salesperson information associated with the product and order line.
     */
    async get_salesperson() {
        if (typeof this.id !== "string") {
            const data = await rpc("/get_pos_sales_person", {
                product_id: this.product_id.id,
                pos_order_line_id: this.id,
            });

            if (data.sales_person) {
                this.salesperson = data.sales_person;
            }
        }
    },
    /**
     * Returns the data needed to display the order line.
     * Extends the base display data with salesperson and user_id.
     */
    getDisplayData() {
        return {
            ...super.getDisplayData(),
            salesperson: this.salesperson || "",
            user_id: this.user_id || null,
        };
    },

});
