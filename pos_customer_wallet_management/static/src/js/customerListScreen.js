/** @odoo-module */
import { PartnerLine } from "@point_of_sale/app/screens/partner_list/partner_line/partner_line";
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { _t } from "@web/core/l10n/translation";
import { RechargeScreen } from "./wallet_recharge";
import { useService } from "@web/core/utils/hooks";

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        this.loadServer()
        this["account_journal"] = [];
    },

    async loadServer() {
        const model_data = this.data['account.journal'];
        if (model_data && model_data.data) {
            this.account_journal = model_data.data;
        } else {
            this.account_journal = [];
        }
    }
});

patch(PartnerLine.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialog = useService("dialog");
        this.pos = useService("pos");
    },

    onClickWallet(ev) {
        if (ev) {
            ev.stopPropagation();
        }

        const partner = this.props.partner;
        if (!partner) {
            console.error("Partner is not defined");
            return;
        }
        const data = this.pos.account_journal || [];

        this.dialog.add(RechargeScreen, {
            title: _t("Wallet Recharge"),
            partner: partner,
            data: data,
        });

    }
});
