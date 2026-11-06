import { PartnerLine } from "@point_of_sale/app/screens/partner_list/partner_line/partner_line";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { RechargeScreen } from "./wallet_recharge";
import { useService } from "@web/core/utils/hooks";

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

        this.dialog.add(RechargeScreen, {
            title: _t("Wallet Recharge"),
            partner: partner,
        });

    }
});
