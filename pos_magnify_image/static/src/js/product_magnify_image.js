import { patch } from "@web/core/utils/patch";
import { ProductCard } from "@point_of_sale/app/components/product_card/product_card";
import { MagnifyProductPopup } from "@pos_magnify_image/js/MagnifyProductPopup";

patch(ProductCard.prototype, {
    onProductMagnifyClick() {
        const productData = this.props.product;
        if (!productData || !productData.id) {
            console.error("Product ID not found in props:", this.props);
            return;
        }
        this.env.services.dialog.add(MagnifyProductPopup, { product: productData });
    },
});
