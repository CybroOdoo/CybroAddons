odoo.define('pos_order_question.OrderQuestionPos', function(require){
     "use strict";
// To load new model 'meals.planning' to pos
     var models = require('point_of_sale.models');
     var _super_orderline = models.Orderline.prototype;
     models.load_fields('product.product', 'order_question_ids');
     models.Orderline = models.Orderline.extend({
            initialize:function(attr,options){
                 var line =_super_orderline.initialize.apply(this,arguments);
                 this.order_question_ids = this.product.order_question_ids;
            }
     })
        models.load_models([{
            model: 'pos.order.question',
            fields: ['name'],
            // Load specific fields from this model based on a domain filter,
            loaded: function(self, order_question) {
            self.order_questions = order_question;
            },
    }]);
});
