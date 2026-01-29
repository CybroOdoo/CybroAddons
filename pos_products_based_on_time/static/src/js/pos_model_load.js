odoo.define('pos_products_based_on_time.planning', function(require){
     "use strict";
// To load new model 'meals.planning' to pos
     var models = require('point_of_sale.models');
        models.load_models([{
            model: 'meals.planning',
            fields: ['time_from', 'time_to','product_ids','state','pos_ids'],
            // The domain filter function checks for records where the given
            //  conditions are satisfied
            domain: function(self){
                return ['&',['state','=','activated'],
                ['pos_ids','in',self.config_id]];
            },
            // Load specific fields from this model based on a domain filter,
            loaded: function(self, meals) {
            self.meals_planning = meals;
            },
    }]);
});
