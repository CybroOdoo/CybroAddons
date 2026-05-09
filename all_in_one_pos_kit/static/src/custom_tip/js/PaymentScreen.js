/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(PaymentScreen.prototype, {
    async CustomTipButton() {
        const resConfig = this.pos.res_config_settings;
        const custom_tip_percentage = resConfig && resConfig.length > 0 ? resConfig[resConfig.length - 1].custom_tip_percentage : 0;

        if (custom_tip_percentage) {
            const currentTotal = this.currentOrder.get_total_with_tax();
            const cust_tip = (currentTotal * parseFloat(custom_tip_percentage) / 100);

            const { confirmed, payload } = await this.showPopup('NumberPopup', {
                title: cust_tip ? _t('Change Tip') : _t('Add Tip'),
                startingValue: cust_tip,
                isInputSelected: true,
            });

            if (confirmed) {
                this.currentOrder.set_tip(parseFloat(payload));
            }
        }
    },

    get customTipInfo() {
        const resConfig = this.pos.res_config_settings;
        const custom_tip_percentage = resConfig && resConfig.length > 0 ? resConfig[resConfig.length - 1].custom_tip_percentage : 0;
        return {
            tip: custom_tip_percentage,
            tip_enable: !!custom_tip_percentage,
        };
    }
});