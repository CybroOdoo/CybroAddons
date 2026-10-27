import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { patch } from "@web/core/utils/patch";

/**
 * Add the product id to the display data of the order line, so that the
 * product image can be shown in the order line of the POS.
 */
patch(PosOrderline.prototype, {
    getDisplayData() {
        return {
            ...super.getDisplayData(...arguments),
            productId: this.product_id.id,
        };
    },
});
