import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

// Patching PosOrder for getting the category of the added products
patch(PosOrder.prototype, {
    // Function to return orderlines with its category
  getCategoryData() {
    const lines = [...this.getOrderlines()];
    const groupedObjects = lines.reduce((acc, line) => {
        const { product_id } = line;
        // Determine category
        let categoryId = null;
        let categoryName = "";

        if (product_id.pos_categ_ids && product_id.pos_categ_ids.length > 0) {
            const category = product_id.pos_categ_ids[0];
            categoryId = category.id;
            categoryName = category.name;
        }

        // Initialize group if not exists
        if (!acc[categoryId || ""]) {
            acc[categoryId || ""] = {
                category_id: categoryId,
                category_name: categoryName,
                subtotal: 0,
                lines: [],
            };
        }

        // Add line and subtotal
        const group = acc[categoryId || ""];
        group.lines.push(line);

        // Add subtotal from line’s price_subtotal_incl (ensure numeric)
        const subtotal = parseFloat(line.price_subtotal_incl || 0);
        group.subtotal += subtotal;

        return acc;
    }, {});

    // Convert the grouped object into a list
    const result = Object.values(groupedObjects);
    return result;

}})

