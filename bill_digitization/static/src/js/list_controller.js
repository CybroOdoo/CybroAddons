/** @odoo-module */
import { ListController } from '@web/views/list/list_controller';
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
patch(ListController.prototype, {
/**
 * This function will used to hide the selected options from the list view
 */
    async  setup() {
        super.setup(...arguments);
        this.state = useState({
     button_state : false
     })
     this.actionService = useService("action");
     this.orm = useService("orm");
     const digitizeBillParam = await this.env.services.orm.silent.call(
                        'ir.config_parameter',
                        'get_param',
                        ["bill_digitization.digitize_bill"],
                    );
     this.state.button_state = digitizeBillParam
    },
    /* Opening a wizard on button click */
    onClickDigitize() {
         this.actionService.doAction({
            name: _t("Upload Bill"),
            type: "ir.actions.act_window",
            res_model: "digitize.bill",
            view_type : 'form',
            view_mode : 'form',
            views: [[false, "form"]],
            target: 'new',
        });
        },
});