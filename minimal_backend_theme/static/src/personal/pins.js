import { EventBus } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { session } from "@web/session";

/**
 * Menus the user pinned (star in the search results and the sidebar), kept
 * on the server per user (model minimal_backend_theme.menu_pin). Components
 * showing pins re-render on the bus' "PINS-CHANGED" event.
 */
export const pinsService = {
    start() {
        const bus = new EventBus();
        let pinnedIds = [...(session.minimal_backend_theme?.pinned_menu_ids || [])];
        return {
            bus,
            get ids() {
                return pinnedIds;
            },
            isPinned(menuId) {
                return pinnedIds.includes(menuId);
            },
            async toggle(menuId) {
                pinnedIds = await rpc("/web/dataset/call_kw/minimal_backend_theme.menu_pin/toggle_pin", {
                    model: "minimal_backend_theme.menu_pin",
                    method: "toggle_pin",
                    args: [menuId],
                    kwargs: {},
                });
                bus.trigger("PINS-CHANGED", { ids: pinnedIds });
                return pinnedIds;
            },
        };
    },
};
registry.category("services").add("minimal_backend_theme.pins", pinsService);
