import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component, useState } from "@odoo/owl";


export class InvoicingScreen extends Component {
    static components = { InvoicingScreen, Dialog };
    static template = "InvoicingScreen";
    static props = {
        invoices: { type: Array },
        title: { type: String, optional: true },
        close: { type: Function },
    };

    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");
        this.state = useState({
            invoices: this.props.invoices,
        });
    }

    async refreshInvoices() {
        this.state.invoices = await this.orm.call("account.move", "get_invoices", []);
    }

    async registerPayment(ev) {
        //Method to print the receipt
        let invoice_id = parseInt(ev['invoice_id'])
        await this.orm.call("account.move", "register_payment",  [invoice_id]);
        await this.refreshInvoices();
    }

    async Confirm(ev) {
        let invoice_id = parseInt(ev['invoice_id'])
        await this.orm.call("account.move", "post_invoice",  [invoice_id]);
        await this.refreshInvoices();
    }
}
