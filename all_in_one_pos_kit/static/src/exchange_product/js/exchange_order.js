/** @odoo-module **/
import { Dialog } from "@web/core/dialog/dialog";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";

export class ExchangeOrder extends Component {
    static template = 'ExchangeOrder';
    static components = { Dialog };
    static props = {
        order_line: { type: Array },
        pos: { type: Object },
        order_id: { type: Number },
        close: { type: Function, optional: true },
        getPayload: { type: Function, optional: true },
    };
    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
    }
    cancel() {
        this.props.close();
    }
    async confirm() {
        for (var i = 0; i < this.props.order_line.length; i++) {
            var line = this.props.order_line[i];
            var product = this.pos.models['product.product'].get(line.product_id);
            if (product) {
                await this.pos.addLineToCurrentOrder(
                    { product_id: product, qty: -line.qty },
                    {},
                    false
                );
            }
        }
        await this.orm.write("pos.order", [this.props.order_id], {
            exchange: true,
        });
        this.pos.showScreen('ProductScreen');
        this.props.close();
    }
}
