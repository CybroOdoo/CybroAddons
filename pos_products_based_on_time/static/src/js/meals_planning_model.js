/** @odoo-module */

import { Base } from "@point_of_sale/app/models/related_models";
import { registry } from "@web/core/registry";
/**
 * Represents the meals planning model for the Point of Sale.
 * This model is responsible for managing meal-related data synchronized from the backend.
 */
export class MealsPlanning extends Base {
    static pythonModel = "meals.planning";
    static enableLazyGetters = false;
}

registry.category("pos_available_models").add(MealsPlanning.pythonModel, MealsPlanning);
