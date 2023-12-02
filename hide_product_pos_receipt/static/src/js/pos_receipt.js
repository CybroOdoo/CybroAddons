odoo.define('hide_product_pos_receipt.receipt', function (require) {
    "use strict";
    /* Extend the orderline and load the field to pos model product */
    var models=require('point_of_sale.models');
    models.load_fields('product.product', 'hide_receipt');
    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({ //extend the orderline and Add a new field
         export_for_printing: function() {
             var line = _super_orderline.export_for_printing.apply(this,arguments);
             line.hide_receipt = this.get_product().hide_receipt;
             return line;
         }
    })
});
