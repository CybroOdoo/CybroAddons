/** @odoo-module */
import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
patch(Order.prototype, {
    export_for_printing() {
        const lines = [...this.orderlines];
        const groupedObjects = lines.reduce((acc, line) => {
            const { product } = line;
            // Check if product has pos_categ_ids and it's not empty
            if (product.pos_categ_ids && product.pos_categ_ids.length > 0) {
                const categoryId = product.pos_categ_ids[0];
                const categoryName = this.pos.db.category_by_id[categoryId].name;
                // Check if category already exists in accumulator, if not, create a new entry
                if (!acc[categoryName]) {
                    acc[categoryName] = { category_name: categoryName, lines: [] };
                }
                // Push the current object into the corresponding category array
                acc[categoryName].lines.push(line);
            }
            return acc;
        }, {});
        // Convert the groupedObjects object into an array of values
        const result = Object.values(groupedObjects);
        // Super the export_for_printing() function
        const orderlines = super.export_for_printing();
        return {
            ...orderlines,
            orderlines: result,
        };
    },
});
