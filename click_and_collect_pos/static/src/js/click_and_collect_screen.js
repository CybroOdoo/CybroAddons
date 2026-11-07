import { Component, proxy, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { BackButton } from "@point_of_sale/app/screens/product_screen/action_pad/back_button/back_button";
import { patch } from "@web/core/utils/patch";
import { ComboSuggestion } from "@point_of_sale/app/models/utils/combo_suggestion";

patch(ComboSuggestion.prototype, {
    _getProductOrderMap(order) {
        if (!order) {
            return {};
        }
        return super._getProductOrderMap(order);
    }
});

export class SaleOrderScreen extends Component {
    static template = "click_and_collect_pos.SaleOrderScreen";
    static components = { BackButton };
    static props = {
        orderUuid: { type: String, optional: true },
    };

    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
        this.state = proxy({
            lines: [],
            loading: true,
            error: null,
            confirming: {},
        });
        this._unsubscribeBus = null;
        onWillStart(async () => {
            await this._fetchPendingLines();
            if (this.pos?.data?.connectWebSocket) {
                this.pos.data.connectWebSocket(
                    "POS_COLLECT_ORDER",
                    () => this._fetchPendingLines()
                );
            }
        });
        onMounted(() => {
            if (this.env.services.bus_service) {
                this.env.services.bus_service.addChannel("POS_COLLECT_ORDER");
                this._unsubscribeBus = this.env.services.bus_service.subscribe(
                    "POS_COLLECT_ORDER",
                    () => this._fetchPendingLines()
                );
            }
        });
        onWillUnmount(() => {
            if (this._unsubscribeBus) {
                this._unsubscribeBus();
            }
        });
    }

    back() {
        let order = this.pos.getOrder();
        if (!order) {
            order = this.pos.addNewOrder();
        }
        this.pos.navigate("ProductScreen", {
            orderUuid: order.uuid,
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
            const companyId = this.pos.company?.id || this.pos.config.company_id?.[0] || this.pos.config.company_id;

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

            const saleOrderLines = await this.orm.searchRead(
                "sale.order.line",
                domain,
                ['id'],
            );

            if (!saleOrderLines.length) {
                this.state.lines = [];
                return;
            }

            const lineIds = saleOrderLines.map(l => l.id);

            const pendingData = await this.orm.call(
                "stock.picking",
                "action_stock_picking",
                [lineIds],
                { pos_config_id: sessionId },
            );

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
            const success = await this.orm.call(
                "stock.picking",
                "action_confirmation_click",
                [parseInt(orderLineIdStr, 10)],
            );

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
    route: "/pos/ui/sale_order/{string:orderUuid}",
    params: {
        orderUuid: true,
    }
});