odoo.define('pos_products_based_on_time.planning', function(require){
     "use strict";
// To load new model 'meals.planning' to pos
     var models = require('point_of_sale.models');
        models.load_models([{
        model: 'meals.planning',
        fields: ['time_from', 'time_to','product_ids','state','pos_ids'],
        domain: function(self){
            return
            ['&',['state','=','activated'],['pos_ids','in',self.config_id]];
        },
        loaded: function(self, meals) {
        self.meals_planning = meals;
            // Perform any additional actions after the model is loaded
        },
    }]);
});