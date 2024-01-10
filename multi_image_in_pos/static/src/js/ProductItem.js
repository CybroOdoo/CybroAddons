//ProductItem icon
odoo.define('multi_image_in_pos.ProductItemButton', function (require) {
    "use strict";
    const ProductItem = require('point_of_sale.ProductItem');
    const Registries = require('point_of_sale.Registries');
    const ProductItemButton = (ProductItem) => class ProductItemButton
        extends ProductItem {
            // Click function of image icon on product item
            // it displays a custom popup
            onClickImageIcon(ev) {
                ev.stopPropagation();
                const product = this.props.product;
                this.showPopup("MultiImagePopup", {
                    data : product.image_ids,
                    product: product,
                });
            }
    }
    ProductItemButton.template = 'ShowProductImages';
    Registries.Component.extend(ProductItem, ProductItemButton);
});
