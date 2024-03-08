/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);},
           /**
           * Override the _processData method to preprocess the meals planning data
           * before it is saved to the global state.
           * @param {Object} loadedData - The data loaded from the backend.
           */
          async _processData(loadedData) {
            await super._processData(...arguments);
            let new_meal = []
            loadedData['meals.planning'].forEach((data) => {
                data.menu_product_ids = loadedData['product.product'].filter((meal) => data.menu_product_ids.includes(meal.id))
                new_meal.push(data)
            })
            this.meals_planning = new_meal
    },
});
