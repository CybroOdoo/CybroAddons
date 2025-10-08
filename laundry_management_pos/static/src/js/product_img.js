odoo.define('laundry_management_pos.pos_order_line', function(require) {
"use strict";

    const { Orderline } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');

    //    Extend the order lines for getting the product images
    const PosSaleOrderline = (Orderline) => class PosSaleOrderline extends Orderline {
        // Product images uploading to the particular field
        get_product_image(){
            const product = this.product;
            return `/web/image?model=product.product&field=image_128&id=${product.id}&write_date=${product.write_date}&unique=1`;
        }
    };
Registries.Model.extend(Orderline, PosSaleOrderline);
return PosSaleOrderline;
});
