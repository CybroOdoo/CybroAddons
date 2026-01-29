odoo.define('laundry_management_pos.pos_order_line', function(require) {
"use strict";

var models = require('point_of_sale.models');

//    Extend the order lines for getting the product images
models.Orderline = models.Orderline.extend({

//  Product images uploading to the particular field
    get_product_image: function(){
        const product = this.product;
        return `/web/image?model=product.product&field=image_128&id=${product.id}&write_date=${product.write_date}&unique=1`;
    },
});
});