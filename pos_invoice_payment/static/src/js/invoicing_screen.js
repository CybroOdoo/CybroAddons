import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { PartnerLine } from "@point_of_sale/app/screens/partner_list/partner_line/partner_line";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { Input } from "@point_of_sale/app/components/inputs/input/input";
import { Component, useState } from "@odoo/owl";


export class InvoicingScreen extends Component {
    static components = { InvoicingScreen, Dialog };
    static template = "InvoicingScreen";
    static props = {
        title: { type: String, optional: true },
        invoices: { type: Array },
        fetchData: { type: Function },
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
    async registerPayment(ev) {
        try {
            let invoice_id = parseInt(ev['invoice_id']);
            await this.orm.call("account.move", "register_payment", [invoice_id]);

            // Check if component is still alive before updating state
            if (this.state && this.state.invoices) {
                const invoice = this.state.invoices.find(inv => inv.invoice_id === invoice_id);
                if (invoice) {
                    invoice.payment_state = 'paid';
                    invoice.amount_residual = 0;
                }
            }
            if (this.props.fetchData) {
                await this.props.fetchData();
            }
        } catch (error) {
            if (error?.message?.includes("destroyed")) {
                return;
            }
            throw error;
        }
    }

    async Confirm(ev) {
        try {
            let invoice_id = parseInt(ev['invoice_id']);
            await this.orm.call("account.move", "post_invoice", [invoice_id]);

            // Check if component is still alive before updating state
            if (this.state && this.state.invoices) {
                const invoice = this.state.invoices.find(inv => inv.invoice_id === invoice_id);
                if (invoice) {
                    invoice.state = 'posted';
                }
            }
            if (this.props.fetchData) {
                await this.props.fetchData();
            }
        } catch (error) {
            if (error?.message?.includes("destroyed")) {
                return;
            }
            throw error;
        }
    }
}
