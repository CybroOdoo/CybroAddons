import { reactive } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { MagnifyProductPopup } from "@pos_magnify_image/js/MagnifyProductPopup";
//Inside ProductsWidget adding clickMagnifyProduct function for magnify image
patch(ProductCard.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialog = useService("dialog");
    },
    async onProductMagnifyClick(product){
        this.magnifyProduct = true;
        this.dialog.add(MagnifyProductPopup, {product: this.props})
    }
});
