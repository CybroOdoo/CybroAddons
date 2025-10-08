odoo.define('advanced_loyalty_management.pos_loyalty_deduction_receipt', function (require) {
"use strict";
var { Order } = require('point_of_sale.models');
const Registries = require('point_of_sale.Registries');

const  DeductedLoyalty = (Order) => class DeductedLoyalty extends Order {
    export_for_printing() {
     //----to show the deducted points in receipt
        var line = super.export_for_printing(...arguments);
            var points = this.pos.lostPoints
            line.lostPoints = points
        return line;
    }
}
Registries.Model.extend(Order, DeductedLoyalty);
})
