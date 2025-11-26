/** @odoo-module */
import { PartnerLine } from "@point_of_sale/app/screens/partner_list/partner_line/partner_line";
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { _t } from "@web/core/l10n/translation";
import { RechargeScreen } from "./wallet_recharge";

patch(PosStore.prototype, {
          async _processData(loadedData){
            await super._processData(...arguments);
            this.account_journal = loadedData['account.journal'];
            this.res_partner = loadedData['res.partner'];
            this.pos_payment_method = loadedData['pos.payment.method'];
          },
});
patch(PartnerLine.prototype, {
    setup() {
        super.setup(...arguments);
    },
    async onClickWallet() {
       var partner = this.props.partner;
       var data = this.env.services.pos.account_journal;
       const { confirmed } = await this.env.services.popup.add(RechargeScreen, {
            title: _t("RechargeScreen"),
            partner: partner,
            data: data,
       });
    }
});