/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";

export class SaleOrderScreen extends Component {
    static template = "SaleOrderScreen";
    static props = {};

    setup() {
        this.pos = usePos();
        this.state = useState({
            lines: [],
            loading: true,
            error: null,
            confirming: {},
        });
        onWillStart(() => this._fetchPendingLines());
    }

    back() {
        this.pos.navigate("ProductScreen", {
            orderUuid: this.pos.getOrder()?.uuid,
        });
    }

    _str(val) {
        if (val === null || val === undefined) return '';
        return '' + val;
    }

    async _fetchPendingLines() {
        this.state.loading = true;
        this.state.error = null;
        try {
            const sessionId = this.pos.config.id;

            const saleOrderLines = await rpc("/web/dataset/call_kw", {
                model: "sale.order.line",
                method: "search_read",
                args: [[
                    ['is_click_and_collect', '=', true],
                    ['state', '=', 'sale'],
                    ['pos_config_id', '=', sessionId],
                ]],
                kwargs: { fields: ['id'] },
            });

            if (!saleOrderLines.length) {
                this.state.lines = [];
                return;
            }

            const lineIds = saleOrderLines.map(l => l.id);

            const pendingData = await rpc("/web/dataset/call_kw", {
                model: "stock.picking",
                method: "action_stock_picking",
                args: [lineIds],
                kwargs: { pos_config_id: sessionId },
            });

            if (pendingData.length && pendingData[0].error) {
                this.state.error = pendingData[0].error;
                return;
            }

            this.state.lines = pendingData.map(d => ({
                id: d.id,
                idStr: '' + d.id,
                order_id: this._str(d.order_id),
                partner_id: this._str(d.partner_id),
                product_id: this._str(d.product_id),
                product_uom_quantity: this._str(d.product_uom_quantity),
            }));

        } catch (err) {
            console.error("[CNC] _fetchPendingLines error:", err);
            this.state.error = err.message || '' + err;
        } finally {
            this.state.loading = false;
        }
    }

    async onClick(ev) {
        ev.stopPropagation();

        const btn = ev.target.closest("button[data-id]");
        if (!btn) return;

        const orderLineIdStr = btn.dataset.id;
        if (!orderLineIdStr) return;

        if (this.state.confirming[orderLineIdStr]) return;

        this.state.confirming[orderLineIdStr] = true;
        this.state.lines = this.state.lines.filter(l => l.idStr !== orderLineIdStr);

        try {
            const success = await rpc("/web/dataset/call_kw", {
                model: "stock.picking",
                method: "action_confirmation_click",
                args: [parseInt(orderLineIdStr, 10)],
                kwargs: {},
            });

            if (success) {
                this.env.services.notification.add(
                    "Click & Collect confirmed — delivery marked as Done",
                    { type: "success" }
                );
            } else {
                this.env.services.notification.add(
                    "Could not confirm: no pending picking found for this line",
                    { type: "warning" }
                );
            }

        } catch (error) {
            console.error("[CNC] action_confirmation_click error:", error);
            this.env.services.notification.add(
                "Error confirming order: " + (error.message || error),
                { type: "danger" }
            );
        } finally {
            delete this.state.confirming[orderLineIdStr];
            await this._fetchPendingLines();
        }
    }
}

registry.category("pos_pages").add("SaleOrderScreen", {
    name: "SaleOrderScreen",
    component: SaleOrderScreen,
    route: "/pos/ui/sale_order",
});