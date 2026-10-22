/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

patch(PosStore.prototype, {
    /**
     * Override the productsToDisplay getter method to filter the list of products
     * based on the current time and the meals planning data.
     * @returns {Array} A sorted array of product objects to be displayed.
     */
    get productsToDisplay() {
        let list = super.productsToDisplay;
        // Get current time in minutes since midnight
        const date = new Date();
        const timeInMinutes = date.getHours() * 60 + date.getMinutes();
        const data = [];
        const meals = this.models["meals.planning"]?.getAll() || [];
        const getTmplId = (mealId) => {
            const mealIdNum = typeof mealId === "object" ? mealId.id : mealId;
            const productRecord = this.models["product.product"]?.get(mealIdNum);
            if (!productRecord) {
                return mealIdNum;
            }
            const pTmpl = productRecord.product_tmpl_id;
            if (!pTmpl) {
                return mealIdNum;
            }
            if (typeof pTmpl === "object" && pTmpl !== null) {
                if (pTmpl.id) {
                    return pTmpl.id;
                }
                if (Array.isArray(pTmpl) && pTmpl.length > 0) {
                    return pTmpl[0];
                }
            }
            return pTmpl;
        };
        meals.forEach((object) => {
            if (object.state !== "activated") {
                return;
            }
            const timeFromInMinutes = object.time_from * 60;
            const timeToInMinutes = object.time_to * 60;
            // Handle times that cross midnight (for example 22:00 to 02:00)
            let inRange = false;
            if (timeFromInMinutes <= timeToInMinutes) {
                inRange = timeFromInMinutes <= timeInMinutes && timeInMinutes < timeToInMinutes;
            } else {
                inRange = timeInMinutes >= timeFromInMinutes || timeInMinutes < timeToInMinutes;
            }
            if (inRange) {
                const planArr = object.menu_product_ids || [];
                Array.from(planArr).forEach((meal) => {
                    data.push(getTmplId(meal));
                });
            }
        });
        if (data.length) {
            list = list.filter((product) => data.includes(product.id));
        } else if (meals.some((m) => m.state === "activated")) {
            const restrictedProductIds = new Set();
            meals.forEach((m) => {
                if (m.state === "activated" && m.menu_product_ids) {
                    Array.from(m.menu_product_ids).forEach((meal) => {
                        restrictedProductIds.add(getTmplId(meal));
                    });
                }
            });
            list = list.filter((product) => !restrictedProductIds.has(product.id));
        }
        return list;
    },
});
