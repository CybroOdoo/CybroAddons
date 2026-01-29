odoo.define('laundry_management_pos.receipt', function(require){
    "use strict";
var models = require('point_of_sale.models');
var _super_orderline = models.Orderline.prototype;

// Extends the order-line used to add the Washing Details in the order receipts
models.Orderline = models.Orderline.extend({

// Used to add the Washing Details in the order receipt
    export_for_printing: function(){
        var line = _super_orderline.export_for_printing.apply(this, arguments);
        line.service_type = this.get_washingType();
        return line;
    }
});
});