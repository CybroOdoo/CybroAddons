import { Navbar } from "@point_of_sale/app/components/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { proxy, onMounted, onWillUnmount } from "@odoo/owl";

patch(Navbar.prototype, {
    setup() {
        super.setup(...arguments);
        this.collectState = proxy({ pendingCount: 0 });
        this._collectPollTimer = null;
        this._unsubscribeBus = null;
        onMounted(() => {
            this._refreshPendingCount();
            if (this.pos?.data?.connectWebSocket) {
                this.pos.data.connectWebSocket(
                    "POS_COLLECT_ORDER",
                    () => this._refreshPendingCount()
                );
            }
            if (this.env.services.bus_service) {
                this.env.services.bus_service.addChannel("POS_COLLECT_ORDER");
                this._unsubscribeBus = this.env.services.bus_service.subscribe(
                    "POS_COLLECT_ORDER",
                    () => this._refreshPendingCount()
                );
            }
        });
        onWillUnmount(() => {
            if (this._collectPollTimer) {
                clearInterval(this._collectPollTimer);
            }
            if (this._unsubscribeBus) {
                this._unsubscribeBus();
            }
        });
        // Auto-refresh badge every 30 seconds
        this._collectPollTimer = setInterval(
            () => this._refreshPendingCount(), 30000
        );
    },

    /**
     * Fetch how many C&C lines are still pending for this POS store
     * and update the badge count.
     */
    async _refreshPendingCount() {
        try {
            const sessionId = this.pos.config.id;
            const companyId = this.pos.company?.id || this.pos.config.company_id?.[0] || this.pos.config.company_id;
            const orm = this.env.services.orm;

            const domain = [
                ['is_click_and_collect', '=', true],
                ['state', '=', 'sale'],
            ];
            if (companyId) {
                domain.push(
                    '|',
                    ['pos_config_id', '=', sessionId],
                    '&',
                    ['pos_config_id', '=', false],
                    ['company_id', '=', companyId]
                );
            } else {
                domain.push(['pos_config_id', '=', sessionId]);
            }

            const lines = await orm.searchRead(
                "sale.order.line",
                domain,
                ['id'],
            );

            if (!lines.length) {
                this.collectState.pendingCount = 0;
                return;
            }

            const lineIds = lines.map(l => l.id);
            const pending = await orm.call(
                "stock.picking",
                "action_stock_picking",
                [lineIds],
                { pos_config_id: sessionId },
            );

            this.collectState.pendingCount =
                (pending[0]?.error) ? 0 : pending.length;
        } catch {
            this.collectState.pendingCount = 0;
        }
    },

    /**
     * Navigate to SaleOrderScreen.
     */
    async onClick() {
        try {
            if (this.pos.navigate) {
                const order = this.pos.getOrder();
                this.pos.navigate("SaleOrderScreen", {
                    orderUuid: order ? order.uuid : undefined,
                });
            } else {
                this.env.services.notification.add(
                    "Navigation error: pos.navigate not available",
                    { type: "danger" }
                );
            }
        } catch (error) {
            this.env.services.notification.add(
                "Error: " + (error.message || error),
                { type: "danger" }
            );
        }
    },
});