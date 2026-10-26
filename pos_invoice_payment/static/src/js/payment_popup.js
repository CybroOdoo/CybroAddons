import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { Component, proxy } from "@odoo/owl";

export class CreatePaymentPopup extends Component {
    static template = "pos_invoice_payment.CreatePaymentPopup";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        journals: { type: Array, optional: true },
        journal_length: { type: Array, optional: true },
        partner_id: { type: Number, optional: true },
        currency_id: { type: Number, optional: true },
        confirmText: { type: String, optional: true },
        close: { type: Function },
    };

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
        const defaultJournalId = this.props.journals && this.props.journals.length > 0 ? this.props.journals[0].id : "";
        this.state = proxy({
            amount: "",
            journalId: defaultJournalId,
        });
    }

    async confirm() {
        const amountVal = parseFloat(this.state.amount);
        if (!amountVal || amountVal <= 0) {
            this.notification.add("Please enter a valid payment amount.", { type: "warning" });
            return;
        }

        const journalId = parseInt(this.state.journalId || (this.props.journals && this.props.journals[0] && this.props.journals[0].id));
        if (!journalId) {
            this.notification.add("Please select a valid journal.", { type: "warning" });
            return;
        }

        const values = {
            partner_id: this.props.partner_id,
            currency_id: this.props.currency_id,
            amount: amountVal,
            journal_id: journalId,
        };

        try {
            await this.orm.call("account.payment", "create_payment", [values]);
            this.notification.add("Payment created successfully.", { type: "success" });
            this.props.close();
        } catch (error) {
            this.notification.add(error?.message || "Failed to create payment.", { type: "danger" });
        }
    }

    cancel() {
        this.props.close();
    }
}
