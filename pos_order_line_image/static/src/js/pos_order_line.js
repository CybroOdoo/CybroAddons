odoo.define('pos_order_line_image.pos_order_line', function(require) {
"use strict";

var models = require('point_of_sale.models');



models.Orderline = models.Orderline.extend({

    get_product_image: function(){
        const product = this.product;
        return `/web/image?model=product.product&field=image_128&id=${product.id}&write_date=${product.write_date}&unique=1`;

    },

});

});
