/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { _t } from "@web/core/l10n/translation";

export class CreatePaymentPopup extends Component {
    // Extending AbstractAwaitablePopup And Adding A Popup
    static template = 'CreatePaymentPopup';
    static components = { Dialog };
    static props = {
        title: { type: String },
        confirmText: { type: String, optional: true },
        journals: { type: Array },
        journal_length: { type: Array },
        partner_id: { type: Number },
        currency_id: { type: Number },
        close: { type: Function },
    }
    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");
        this.notification = useService("notification");
    }

    async confirm(ev) {
        let partner_id = ev['partner_id']
        let currency_id = ev['currency_id']
        let amount = document.getElementById("amount").value
        let journal_id = document.getElementById("journal").value

        if (!journal_id) {
            this.notification.add(_t("Please select a journal."), { type: "warning" });
            return;
        }
        if (!amount || Number(amount) <= 0) {
            this.notification.add(_t("Please enter a valid payment amount."), { type: "warning" });
            return;
        }

        var values = {}
        if (partner_id) {
          values["partner_id"] = partner_id;
        }
        if (journal_id) {
          values["journal_id"] = journal_id;
        }
        if (currency_id) {
          values["currency_id"] = currency_id;
        }
        if (amount) {
          values["amount"] = amount;
        }

        await this.orm.call("account.payment", "create_payment",  [values]);
        const currentOrder = this.pos.get_order();
        if (currentOrder) {
            currentOrder.customer_payment_created = true;
        }
        this.notification.add(_t("Payment created."), { type: "success" });
        this.props.close();
    }

    cancel() {
        this.props.close();
    }
}
