/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { ProductsWidget } from "@point_of_sale/app/screens/product_screen/product_list/product_list";
import { MagnifyProductPopup } from "@pos_magnify_image/js/MagnifyProductPopup";

//Inside ProductsWidget adding clickMagnifyProduct function for magnify image
patch(ProductsWidget.prototype, {
    //Supering setup() function
    setup() {
        super.setup(...arguments);
        this.popup = useService("popup");
    },
    //Function for Magnifying the product image
    async clickMagnifyProduct(product) {
        this.magnifyProduct = true;
        const info = await this.pos.getProductInfo(product, 1);
        this.popup.add(MagnifyProductPopup, {
            product: product
        });
        this.magnifyProduct = false;
    },
});
