/** @odoo-module */
import { Order, Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Orderline.prototype, {
    getDisplayData() {
    /**Add the product id to update the image**/
        return {
        	...super.getDisplayData(),
            product_id: this.get_product().id,
            
        };
    }
});
