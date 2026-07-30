/** @odoo-module **/

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
    dependencies: ["rpc"],
    async start(env, { rpc }) {
        // Pre-load offline data in the background after Odoo boots.
        // rpc is injected via the dependencies array — never use this.rpc
        // inside a plain function, as `this` is not the service instance.
        async function syncOfflineData() {
            try {
                const data = await rpc("/web/dataset/call_kw", {
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