odoo.define('pos_products_based_on_time.planning', function(require){
     "use strict";
     var { PosGlobalState } = require('point_of_sale.models');
     const Registries = require('point_of_sale.Registries');
     // Define a new class that extends PosGlobalState
     const planning = (PosGlobalState) => class planning extends PosGlobalState {
           /**
           * Override the _processData method to preprocess the meals planning data
           * before it is saved to the global state.
           * @param {Object} loadedData - The data loaded from the backend.
           */
          async _processData(loadedData) {
            super._processData(...arguments)
            // Process the product_ids field of each meals planning record to include
            // The actual product data instead of just the product ID.
            let new_meal = []
            loadedData['meals.planning'].forEach((data) => {
                data.product_ids = loadedData['product.product'].filter((meal) => data.product_ids.includes(meal.id))
                new_meal.push(data)
            })
            // Update the meals planning data.
            this.meals_planning = new_meal
          }
     }
     // Register the new planning class with the POS registry.
     Registries.Model.extend(PosGlobalState, planning);
});
