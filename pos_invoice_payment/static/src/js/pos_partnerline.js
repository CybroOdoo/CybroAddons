/** @odoo-module **/

import { PartnerLine } from "@point_of_sale/app/screens/partner_list/partner_line/partner_line";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { CreatePaymentPopup } from "@pos_invoice_payment/app/popup/payment_popup";

patch(PartnerLine.prototype, {
    setup() {
        super.setup(...arguments);
        this.popup = useService("popup");
        this.orm = useService("orm");
    },
    async showPop(ev) {
        const partner_id = this.props.partner.id;
        const journals = await this.orm.call("account.journal", "get_journal", []);

        let journal_length = [];
        journals.forEach((j, index) => journal_length.push(index));

        this.popup.add(CreatePaymentPopup, {
            title: "Create Payment",
            journals: journals,
            journal_length: journal_length,
            partner_id: partner_id
        });
    }
});
