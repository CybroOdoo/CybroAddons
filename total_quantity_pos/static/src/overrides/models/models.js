/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    /**
     * Extends the export_for_printing method to customize the printing data.
     * Removes the 'removeLine' property from each order line.
     * @returns {Object} The modified printing data.
     */
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        result.TotalQuantity = this.orderlines.map(item => parseFloat(item["quantity"])).reduce((acc, value) => acc + value, 0);
        result.ItemCount = this.orderlines.length;
        return result;
    },
});
