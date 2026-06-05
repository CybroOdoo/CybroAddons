/** @odoo-module **/
import { PartnerLine } from "@point_of_sale/app/screens/partner_list/partner_line/partner_line";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
import { CreatePaymentPopup } from "./payment_popup";



patch(PartnerLine.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.state = useState({
            partnerId: this.props.partner.id,
            currencyID: this.pos.currency.id,
        });
    },

    async showPop(ev) {
        const partnerId = this.state.partnerId;
        const currencyID = this.state.currencyID;
        const journalLength = [];

        let journalData = await this.orm.call("account.journal", "get_journal",  []);

        console.log('journalData', journalData)

        Object.keys(journalData).forEach(key => {
            journalLength.push(key);
        });

        await this.dialog.add(CreatePaymentPopup, {
            title: _t("Create Payment"),
            confirmText: _t("Exit"),
            journals: journalData,
            currency_id: currencyID,
            journal_length: journalLength,
            partner_id: partnerId
        });
    }
});
