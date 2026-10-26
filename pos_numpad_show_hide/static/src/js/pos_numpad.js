/** @odoo-module **/

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";

patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.state.isNumpadHidden = false;
    },
    toggleNumpad() {
        this.state.isNumpadHidden = !this.state.isNumpadHidden;
    },
});
