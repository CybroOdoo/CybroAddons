odoo.define('multi_barcodes_pos.barcode_search', function(require) {
    "use strict";

    var models = require('point_of_sale.models');

    models.load_models({
     model: 'multi.barcode.products',
        fields: ['id','multi_barcode','product_multi'],
    loaded: function(self, barcodes){
         self.set('multi_barcode',barcodes);
        self.product_barcodes = barcodes;
        self.db.product_barcodes = barcodes;
     },
    },{'before': 'product.product'});
});
