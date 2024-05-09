odoo.define('laundry_management_pos.receipt', function(require){
    "use strict";

    const { Orderline } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    var _super_orderline = Orderline.prototype;
    // Extends the order-line used to add the Washing Details in the order receipts
    const PosSaleOrderline = (Orderline) => class PosSaleOrderline extends Orderline {
    // Used to add the Washing Details in the order receipt
        export_for_printing(){
            var line = _super_orderline.export_for_printing.apply(this, arguments);
            line.service_type = this.get_washingType();
            return line;
    }
}
 Registries.Model.extend(Orderline, PosSaleOrderline);
    return PosSaleOrderline;
});
