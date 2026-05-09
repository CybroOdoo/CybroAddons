/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { PosStore } from "@point_of_sale/app/store/pos_store";

/**
 * Expose the set of currently planned product IDs on the POS store,
 * so the XML template can read it reactively.
 */
patch(PosStore.prototype, {
    get plannedProductData() {
        const date = new Date();
        const hours = date.getHours();
        const minutes = date.getMinutes();
        const time = hours + minutes / 60;
        const ids = new Set();
        const currentConfigId = this.config?.id;
        let hasShopPlans = false;
        
        // Use native Odoo 18 model access
        const mealsModel = this.models['meals.planning'];
        if (!mealsModel) {
            return { ids, hasShopPlans };
        }

        const plans = mealsModel.getAll().filter(p => p.state === 'activated');

        plans.forEach((plan) => {
            const posIdsRaw = plan.pos_ids || [];
            const posIds = posIdsRaw.map(p => typeof p === 'object' ? p.id : p);
            
            const isForThisShop = posIds.includes(currentConfigId);
            if (isForThisShop) {
                hasShopPlans = true;
                const isInTimeRange = plan.time_from <= time && time < plan.time_to;
                
                if (isInTimeRange) {
                    const productIdsRaw = plan.menu_product_ids || [];
                    const productIds = productIdsRaw.map(p => typeof p === 'object' ? p.id : p);
                    productIds.forEach(id => {
                        if (id) ids.add(id);
                    });
                }
            }
        });
        return { ids, hasShopPlans };
    },
    get plannedProductIds() {
        return this.plannedProductData.ids;
    },
});

/**
 * Override productsToDisplay to filter by the active meal plan
 * when the shop has ANY activated plans.
 */
patch(ProductScreen.prototype, {
    get productsToDisplay() {
        // Run the original getter first
        let list = super.productsToDisplay;

        const { ids, hasShopPlans } = this.pos.plannedProductData;
        
        // If this shop has any "Product Planning" records, we ONLY show products from the active one.
        // If no plan is active for the current time but the shop has plans, we show NOTHING (Strict mode).
        if (hasShopPlans) {
            list = list.filter((product) => ids.has(product.id));
        }
        return list;
    },
});
