/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

patch(PosStore.prototype, {
    async setup() {
            await super.setup(...arguments);
        },
           /**
           * Override the _processData method to preprocess the meals planning data
           * before it is saved to the global state.
           * @param {Object} loadedData - The data loaded from the backend.
           */
        async processServerData(loadedData) {
            await super.processServerData(loadedData);
             // Add Payment Interface to Payment Method
             let new_meal = []
             for (const pm of this.data.models["meals.planning"].getAll()) {
                this.menu_product_ids = this.data.models['product.product'].filter((meal) => pm.menu_product_ids.includes(meal.id))
                new_meal.push(pm)
             }
            this.meals_planning = new_meal
            const meals = this.data.models["meals.planning"];
        },
});
