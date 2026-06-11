/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
import { session } from "@web/session";

publicWidget.registry.DeliveryAvailable = publicWidget.Widget.extend({

    selector: ".available",

    events: {
        "click .delivery_available": "_onClickAvailable",
    },

    /**
     * When delivery person clicks "Available"
     */
    async _onClickAvailable(ev) {
        ev.preventDefault();

        try {
            // Call backend method
            const result = await jsonrpc(
                "/web/dataset/call_kw/stock.picking/delivery_available",
                {
                    model: "stock.picking",
                    method: "delivery_available",
                    args: [[]],
                    kwargs: {
                        user_id: session.uid,
                    },
                }
            );
            // Reload page
            window.location.reload();
        } catch (error) {
            console.error("Delivery availability error:", error);
        }
    },
});
