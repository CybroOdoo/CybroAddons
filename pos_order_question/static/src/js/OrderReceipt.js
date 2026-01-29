odoo.define('pos_order_question.OrderQuestion.js', function(require){
    "use strict";
    var models = require('point_of_sale.models');
    //   Extending receipt order line
    models.load_fields('product.product', 'order_question_ids');
    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        export_for_printing: function(){
            //       Supering export_for_printing() to get chose questions in receipt.
            var line = _super_orderline.export_for_printing.apply(this, arguments);
            line.QuestionList = this.QuestionList;
            return line;
        }
    });
});
