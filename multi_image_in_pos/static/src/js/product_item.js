// Extending ProductItem for adding icon for multiple images
odoo.define('multi_image_in_pos.ProductItemButton', function (require) {
    "use strict";
    const ProductItem = require('point_of_sale.ProductItem');
    const Registries = require('point_of_sale.Registries');
    const models = require('point_of_sale.models');
    models.load_fields("product.product", ['image_ids']);
    models.load_fields("product.product", ['is_img_added']);
    models.load_fields("product.template", ['image_ids']);
    models.load_fields("product.template", ['is_img_added']);
    const ProductItemButton = (ProductItem) => class ProductItemButton
        extends ProductItem {
            // Showing popup on clicking icon of multiple images
            onClickImageIcon(ev) {
                ev.stopPropagation();
                const product = this.props.product;
                var image_ids = product.image_ids
                this.showPopup("MultiImagePopup", {
                    data : image_ids,
                    product: product,
                });
            }
    }
    ProductItemButton.template = 'ShowProductImages';
    Registries.Component.extend(ProductItem, ProductItemButton);
});
