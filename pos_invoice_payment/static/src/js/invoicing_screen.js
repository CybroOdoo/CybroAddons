/** @odoo-module **/

import { registry } from "@web/core/registry";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component } from "@odoo/owl";

export class InvoicingScreen extends Component {
    static template = "pos_invoice_payment.InvoicingScreen";

    setup() {
        super.setup();
        this.pos = usePos();
    }

    back() {
        this.pos.showScreen('ProductScreen');
    }

    async registerPayment(data_id) {
        await this.env.services.orm.call(
            "account.move",
            "register_payment",
            [[data_id]]
        );
        this.pos.showScreen('ProductScreen', {});
    }

    async Confirm(data_id) {
        await this.env.services.orm.call(
            "account.move",
            "post_invoice",
            [[data_id]]
        );
        this.pos.showScreen('ProductScreen', {});
    }
}

registry.category("pos_screens").add("InvoicingScreen", InvoicingScreen);
