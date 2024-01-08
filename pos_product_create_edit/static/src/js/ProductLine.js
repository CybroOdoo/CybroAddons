odoo.define("pos_product_create_edit.ProductLine", function(require) {
    "use strict";
    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");
    class ProductLine extends PosComponent {
        /**
         * Get the URL of the product image.
         * @returns {string} The URL of the product image.
         */

        get imageUrl() {
            const product = this.props.product;
            return `/web/image?model=product.product&field=image_128&id=${product.id}&unique=${product.write_date}`;
        }
        /**
         * Open the EditProductPopup to edit the current product.
         */
        async editCurrentProduct() {
            await this.showPopup("EditProductPopup", {
                product: this.props.product,
            });
        }
    }
    ProductLine.template = "ProductLine";
    Registries.Component.add(ProductLine);
    return ProductLine;
});
