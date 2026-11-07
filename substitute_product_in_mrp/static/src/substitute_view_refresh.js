/** @odoo-module **/
/**
 * substitute_view_refresh.js
 *
 * When the server notifies that the substitute product group was granted
 * or revoked for the current user, invalidate the web client's RAM and
 * IndexedDB view-cache for `get_views` so the BOM form re-fetches the
 * correct arch (with or without the Substitute Product column) immediately,
 * without the user having to do a manual hard reload (Ctrl + Shift + R).
 */
import { rpcBus } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";

export const substituteViewRefreshService = {
    dependencies: ["bus_service"],

    start(env, { bus_service }) {
        bus_service.subscribe(
            "substitute_product_in_mrp/refresh_views",
            () => {
                // Clears both the RAM cache and the IndexedDB disk cache
                // for the "get_views" RPC call so the next navigation to
                // any BOM view fetches a fresh arch from the server.
                rpcBus.trigger("CLEAR-CACHES", "get_views");
            },
        );
    },
};

registry
    .category("services")
    .add("substitute_view_refresh", substituteViewRefreshService);
