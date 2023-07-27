odoo.define('hide_product_pos_receipt.receipt', function (require) {
"use strict";
var { Orderline } = require('point_of_sale.models');
const Registries = require('point_of_sale.Registries');
//Extending the models and add the hide_receipt value
const hideproduct = (Orderline) => class hideproduct extends Orderline {
    export_for_printing() {
        var line = super.export_for_printing(...arguments);
        line.product_variant_id = this.product.id;
        line.hide_receipt = this.get_product().hide_receipt;
        return line;
    }
}
Registries.Model.extend(Orderline, hideproduct);
});