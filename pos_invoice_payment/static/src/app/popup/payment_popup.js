/** @odoo-module **/

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";

export class CreatePaymentPopup extends AbstractAwaitablePopup {
    static template = "pos_invoice_payment.CreatePaymentPopup";

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.pos = usePos();
    }

    async confirm() {
        const partner_id = this.props.partner_id;
        const currency_id = this.pos.company.currency_id[0];
        const amount = document.getElementById("amount").value;
        const journal_id = document.getElementById("journal").value;
        
        let values = {};
        if (partner_id) values["partner_id"] = partner_id;
        if (journal_id) values["journal_id"] = parseInt(journal_id);
        if (currency_id) values["currency_id"] = currency_id;
        if (amount) values["amount"] = parseFloat(amount);
        
        await this.orm.call("account.payment", "create_payment", [values]);
        super.confirm();
    }
}
