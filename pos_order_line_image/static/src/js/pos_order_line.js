import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { patch } from "@web/core/utils/patch";

/**
 * Patches the PosOrderline model to include additional display data.
*/
patch(PosOrderline.prototype, {
    /**
     * Extends the original saleDetails method to include the product ID.
     *
     * @returns {Object} The display data for the POS order line, including the product ID.
     */
    saleDetails() {

        return {
            ...super.saleDetails,
             product_id: this.getProduct().id,
        }
    }
});
