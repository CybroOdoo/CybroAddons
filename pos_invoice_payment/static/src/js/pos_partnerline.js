import { PartnerLine } from "@point_of_sale/app/screens/partner_list/partner_line/partner_line";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { proxy } from "@odoo/owl";
import { CreatePaymentPopup } from "./payment_popup";

patch(PartnerLine.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.state = proxy({
            partnerId: this.props.partner.id,
            currencyID: this.pos.currency.id,
        });
    },

    async showPop(ev) {
        const partnerId = this.state.partnerId;
        const currencyID = this.state.currencyID;
        const journalData = await this.orm.call("account.journal", "get_journal", []);

        await this.dialog.add(CreatePaymentPopup, {
            title: "Create Payment",
            confirmText: "Exit",
            journals: journalData,
            currency_id: currencyID,
            partner_id: partnerId,
        });
    },
});
