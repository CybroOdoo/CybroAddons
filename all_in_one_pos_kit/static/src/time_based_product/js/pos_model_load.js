/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

patch(PosStore.prototype, {
    /**
     * Keep the meals planning records loaded from the backend, they are
     * used to filter the products shown in the product screen.
     * @param {Object} loadedData - The data loaded from the backend.
     */
    async processServerData(loadedData) {
        await super.processServerData(loadedData);
        this.meals_planning = this.data.models["meals.planning"].getAll();
    },
});
