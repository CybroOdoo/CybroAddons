/** @odoo-module */
import { ProductInfoPopup } from "@point_of_sale/app/components/popups/product_info_popup/product_info_popup";
import { patch } from "@web/core/utils/patch";
import { onWillStart } from "@odoo/owl";

if (Array.isArray(ProductInfoPopup.props) && !ProductInfoPopup.props.includes("product")) {
    ProductInfoPopup.props.push("product");
} else if (ProductInfoPopup.props && !ProductInfoPopup.props.product) {
    ProductInfoPopup.props.product = { type: Object, optional: true };
}

patch(ProductInfoPopup.prototype, {
    setup() {
        super.setup();
        if (this.pos.config.enable_multi_image){
            onWillStart(() => this.getImages());
        }
    },
    async getImages() {
        let productVariant = this.props.product;
        if (!productVariant && this.props.productTemplate && this.props.productTemplate.product_variant_ids && this.props.productTemplate.product_variant_ids.length > 0) {
            productVariant = this.props.productTemplate.product_variant_ids[0];
        }
        if (!productVariant) {
            console.warn("MultiImagePopup: No product variant found.");
            this.images = [];
            return;
        }

        if (productVariant.image_ids) {
            this.images = productVariant.image_ids;
            return;
        }

        try {
            const res = await this.pos.env.services.orm.searchRead(
                'product.product',
                [['id', '=', productVariant.id]],
                ['image_ids']
            );
            if (res && res.length > 0 && res[0].image_ids) {
                this.images = res[0].image_ids;
            } else {
                this.images = [];
            }
        } catch (error) {
            console.error("Failed to load multi images:", error);
            this.images = [];
        }
    }
});
