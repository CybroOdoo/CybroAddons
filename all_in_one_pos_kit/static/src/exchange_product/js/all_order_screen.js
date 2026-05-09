/** @odoo-module */
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ExchangeOrder } from "./exchange_order";

export class CustomOrderScreen extends Component {
    static template = "CustomOrdrScreen"
    setup() {
        this.orm = useService("orm");
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.state = useState({
            orders: [],
        });
        onWillStart(async () => {
            await this._loadOrders();
        });
    }
    async _loadOrders() {
        // Fetch all completed/paid orders via RPC
        const orders = await this.orm.searchRead(
            "pos.order",
            [['state', 'in', ['paid', 'done', 'invoiced']]],
            ['name', 'pos_reference', 'partner_id', 'date_order', 'lines', 'exchange'],
            { order: 'date_order desc', limit: 100 }
        );
        this.state.orders = orders;
    }
    back() {
        this.pos.showScreen('ProductScreen');
    }
    async _onClickOrder(order) {
        if (order.exchange === true) {
            this.dialog.add(AlertDialog, {
                title: 'Exchange order',
                body: 'Already created the Exchange order'
            });
        } else {
            // order.lines contains line IDs from searchRead
            let lineIds = order.lines;
            let value = await this.orm.call("pos.order.line", "get_product_details", [lineIds]);
            this.dialog.add(ExchangeOrder, {
                order_line: value,
                pos: this.pos,
                order_id: order.id
            });
        }
    }
};
registry.category("pos_screens").add("CustomOrderScreen", CustomOrderScreen);
