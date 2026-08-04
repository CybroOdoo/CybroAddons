/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";

const serviceRegistry = registry.category("services");

/**
 * Service responsible for preloading and caching Offline Sales data.
 */

const offlineHandler = {
     /**
     * Initialize the Offline Sales background synchronization service.
     *
     * A delayed synchronization is scheduled after Odoo startup to
     * retrieve offline data and store it locally for offline access.
     *
     * @param {Object} env - Odoo service environment.
     */
    async start(env) {
        // Pre-load offline data in the background after Odoo boots
        async function syncOfflineData() {
            try {
                const data = await rpc("/web/dataset/call_kw/sale.order/get_offline_data", {
                    model: "sale.order",
                    method: "get_offline_data",
                    args: [],
                    kwargs: {},
                });
                if (data && data.products) {
                    localStorage["offline_sale_db_data"] = JSON.stringify(data);
                    console.info("Offline Sales: Initial data sync complete.");
                }
            } catch (e) {
                console.error("Offline Sales Background Sync Failed:", e);
            }
        }

        // Delay sync so it doesn't slow down Odoo boot
        setTimeout(syncOfflineData, 5000);
    }
};

serviceRegistry.add("offline_sale.main_handler", offlineHandler);
