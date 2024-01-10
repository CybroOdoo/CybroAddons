/** @odoo-module **/
//   Extending receipt order line
var { Orderline } = require('point_of_sale.models');
const Registries = require('point_of_sale.Registries');
const QuestionInOrderline = (Orderline) => class QuestionInOrderline extends Orderline {
    export_for_printing() {
//       Supering export_for_printing() to get chose questions in receipt.
        var line = super.export_for_printing(...arguments);
        line.QuestionList = this.QuestionList;
        return line;
    }
}
Registries.Model.extend(Orderline, QuestionInOrderline);
