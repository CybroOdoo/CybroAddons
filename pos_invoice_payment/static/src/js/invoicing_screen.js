import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { Component, onMounted, proxy } from "@odoo/owl";

export class InvoicingScreen extends Component {
    static components = { Dialog };
    static template = "pos_invoice_payment.InvoicingScreen";
    static props = {
        title: { type: String, optional: true },
        invoices: { type: Array },
        close: { type: Function },
    };

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = proxy({
            invoices: this.props.invoices || [],
        });
        onMounted(() => this.loadInvoices());
    }

    async loadInvoices() {
        try {
            const invoices = await this.orm.call("account.move", "get_invoices", []);
            this.state.invoices = invoices;
        } catch (error) {
            this.notification.add("Failed to load invoices.", { type: "danger" });
        }
    }

    async registerPayment(ev) {
        const invoice_id = typeof ev === "object" && ev !== null ? parseInt(ev.invoice_id) : parseInt(ev);
        if (!invoice_id) {
            this.notification.add("Invalid invoice ID.", { type: "danger" });
            return;
        }
        try {
            await this.orm.call("account.move", "register_payment", [invoice_id]);
            this.notification.add("Payment registered successfully.", { type: "success" });
            await this.loadInvoices();
        } catch (error) {
            if (error?.message?.includes("destroyed")) {
                return;
            }
            this.notification.add(error?.message || "Failed to register payment.", { type: "danger" });
        }
    }

    async confirmInvoice(ev) {
        const invoice_id = typeof ev === "object" && ev !== null ? parseInt(ev.invoice_id) : parseInt(ev);
        if (!invoice_id) {
            this.notification.add("Invalid invoice ID.", { type: "danger" });
            return;
        }
        try {
            await this.orm.call("account.move", "post_invoice", [invoice_id]);
            this.notification.add("Invoice confirmed successfully.", { type: "success" });
            await this.loadInvoices();
        } catch (error) {
            if (error?.message?.includes("destroyed")) {
                return;
            }
            this.notification.add(error?.message || "Failed to confirm invoice.", { type: "danger" });
        }
    }
}
