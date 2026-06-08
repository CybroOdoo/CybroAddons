/** @odoo-module **/
/**
 * Click & Collect – POS Navbar patch
 *
 * Shows a live badge with the count of pending C&C orders for this session.
 * Clicking the button navigates to SaleOrderScreen which fetches its own
 * live data — no data is passed as props.
 */
import { Navbar } from "@point_of_sale/app/components/navbar/navbar";
import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { useState, onMounted, onWillUnmount } from "@odoo/owl";

patch(Navbar.prototype, {
    setup() {
        super.setup(...arguments);
        this.collectState = useState({ pendingCount: 0 });
        this._collectPollTimer = null;
        onMounted(() => this._refreshPendingCount());
        onWillUnmount(() => {
            if (this._collectPollTimer) {
                clearInterval(this._collectPollTimer);
            }
        });
        // Auto-refresh badge every 30 seconds
        this._collectPollTimer = setInterval(
            () => this._refreshPendingCount(), 30000
        );
    },

    /**
     * Fetch how many C&C lines are still pending for this POS session
     * and update the badge count.
     */
    async _refreshPendingCount() {
        try {
            const sessionId = this.pos.config.id;

            const lines = await rpc("/web/dataset/call_kw", {
                model: "sale.order.line",
                method: "search_read",
                args: [[
                    ['is_click_and_collect', '=', true],
                    ['state', '=', 'sale'],
                    ['pos_config_id', '=', sessionId],
                ]],
                kwargs: { fields: ['id'] },
            });

            if (!lines.length) {
                this.collectState.pendingCount = 0;
                return;
            }

            const lineIds = lines.map(l => l.id);
            const pending = await rpc("/web/dataset/call_kw", {
                model: "stock.picking",
                method: "action_stock_picking",
                args: [lineIds],
                kwargs: { pos_config_id: sessionId },
            });

            this.collectState.pendingCount =
                (pending[0]?.error) ? 0 : pending.length;
        } catch {
            this.collectState.pendingCount = 0;
        }
    },

    /**
     * Navigate to SaleOrderScreen.
     * The screen fetches its own live data — no data passed here.
     */
    async onClick() {
        try {
            if (this.pos.navigate) {
                this.pos.navigate("SaleOrderScreen", {});
            } else {
                this.env.services.notification.add(
                    "Navigation error: pos.navigate not available",
                    { type: "danger" }
                );
            }
        } catch (error) {
            console.error("Click & Collect navbar error:", error);
            this.env.services.notification.add(
                "Error: " + (error.message || error),
                { type: "danger" }
            );
        }
    },
});