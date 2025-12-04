import { reactive } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { MagnifyProductPopup } from "@pos_magnify_image/js/MagnifyProductPopup";

patch(ProductCard.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialog = useService("dialog");
    },
    async onProductMagnifyClick(ev) {  // Optional: Add (ev) if needed for event handling
        // Extract the actual product from props (adjust key if it's not 'product')
        const productData = this.props.product;  // Or this.props if product is flat—log to confirm
        if (!productData || !productData.id) {
            console.error("Product ID not found in props:", this.props);  // Debug log
            return;
        }
        this.dialog.add(MagnifyProductPopup, { product: productData });
    }
});